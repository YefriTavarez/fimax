# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr, nowdate
from frappe import _ as __

from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_account_currency, get_balance_on

from fimax.utils import DocStatus

class LoanCharges(Document):
	def validate(self):
		self.validate_amounts()
		self.set_missing_values()

	def on_update_after_submit(self):
		self.validate_amounts()

	def on_submit(self):
		self.update_outstanding_amount()

		if not self.flags.dont_update_gl_entries:
			self.make_gl_entries(cancel=False)
			
	def before_cancel(self):
		if not self.flags.dont_update_gl_entries:
			self.make_gl_entries(cancel=True)

	def update_references(self, cancel=False):
		# list of reference types that don't need to update the outstanding and paid amount
		skipped_list = ["Insurance Card", "GPS Installation"]

		if self.reference_type in skipped_list: return
		
		reference = frappe.get_doc(self.reference_type, self.reference_name)

		if not cancel: pass

		reference.paid_amount = self.get_paid_amount()
		reference.outstanding_amount = self.get_outstanding_amount()

		if hasattr(reference, "validate_amounts"):
			reference.validate_amounts()

		if hasattr(reference, "update_status"):
			reference.update_status()
			
		reference.submit()

	def set_missing_values(self):
		self.outstanding_amount = self.total_amount

	def get_outstanding_amount(self):
		total_amount = frappe.db.get_value("Loan Charges", filters={
			"docstatus": 1,
			"status": ["!=", "Closed"],
			"reference_type": self.reference_type,
			"reference_name": self.reference_name,
		}, fieldname=["SUM(total_amount)"])

		return flt(total_amount, 2) - self.get_paid_amount()

	def get_paid_amount(self):
		paid_amount = frappe.db.get_value("Loan Charges", filters={
			"docstatus": 1,
			"status": ["!=", "Closed"],
			"reference_type": self.reference_type,
			"reference_name": self.reference_name,
		}, fieldname=["SUM(paid_amount)"])

		return flt(paid_amount, 2)

	def update_outstanding_amount(self):
		if not self.docstatus == 1.000:
			frappe.throw(__("Please submit this Loan Charge before updating the outstanding amount!"))
			
		outstanding_amount = flt(self.total_amount) - flt(self.paid_amount)

		if outstanding_amount < 0.000:
			frappe.throw(__("Outstanding amount cannot be negative!"))

		self.outstanding_amount = flt(outstanding_amount, 2)

	def validate_reference_name(self):
		if not self.loan:
			frappe.throw(__("Missing Loan!"))

		if not self.reference_type:
			frappe.throw(__("Missing Repayment Type!"))

		if not self.reference_name:
			frappe.throw(__("Missing Repayment Name!"))

		docstatus = frappe.db.get_value(self.reference_type, 
			self.reference_name, "docstatus")

		if DocStatus(docstatus) is not DocStatus.SUBMITTED:
			frappe.throw(__("Selected {0} is not submitted!".format(self.reference_type)))

	def validate_amounts(self):
		if not flt(self.total_amount):
			frappe.throw(__("Missing amount!"))

		if flt(self.paid_amount, 2) > flt(self.total_amount, 2):
			frappe.throw(__("Paid Amount cannot be greater than Total amount!"))

		if flt(self.outstanding_amount, 2) < 0.000:
			frappe.throw(__("Outstanding Amount cannot be less than zero!"))

	def update_status(self):

		# it's pending if repayment date is in the future and has nothing paid
		if cstr(self.repayment_date) >= nowdate() and self.outstanding_amount > 0.000:
			self.status = "Pending"

		# it's partially paid if repayment date is in the future and has something paid
		if cstr(self.repayment_date) > nowdate() and self.paid_amount > 0.000:
			self.status = "Partially"

		# it's overdue if repayment date is in the past and is not fully paid
		if cstr(self.repayment_date) <= nowdate() and self.outstanding_amount > 0.000:
			self.status = "Overdue"

		# it's paid if paid and total amount are equal hence there's not outstanding amount
		if flt(self.paid_amount, 2) == flt(self.total_amount, 2) or not flt(self.outstanding_amount, 0):
			self.status = "Paid"

	def make_gl_entries(self, cancel=False, adv_adj=False):
		from erpnext.accounts.general_ledger import make_gl_entries
		from erpnext.accounts.utils import get_company_default

		loan_doc = frappe.get_doc(self.meta.get_field("loan").options, self.loan)

		income_account = get_company_default(loan_doc.company, "default_income_account")

		gl_map = loan_doc.get_double_matched_entry(self.total_amount, income_account, 
			voucher_type=self.doctype, voucher_no=self.name)

		make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, merge_entries=False)
	
	def is_elegible_for_deletion(self):
		if self.outstanding_amount == 0 \
			or self.paid_amount > 0: return False
		return True

def on_doctype_update():
	if frappe.flags.in_install == "fimax": return

	# let's drop the view if exists
	frappe.db.sql_ddl("""drop view if exists `viewPaid Fine`""")
	
	# let's create the view
	frappe.db.sql_ddl("""
		create view `viewPaid Fine` as select 
			loan.name as loan,
			loan.party as party,
			charge.repayment_period as repayment,
			(select date(max(t.creation)) from `tabIncome Receipt Items` t where t.voucher_name = charge.name) as fecha,
			charge.total_amount as paid_amount,
			charge.total_amount as total_amount,
			charge.loan_charges_type as type, 
			charge.status as status
		from 
			`tabLoan Charges` as charge
		join 
			`tabLoan` as loan 
		on 
			loan.name = charge.loan
	""")
