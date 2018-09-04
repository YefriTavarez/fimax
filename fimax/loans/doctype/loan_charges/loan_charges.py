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

		if flt(self.outstanding_amount) < 0.000:
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

	def get_double_matched_entry(self, amount, against):
		from erpnext.accounts.utils import get_company_default

		base_gl_entry = {
			"posting_date": self.posting_date,
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"cost_center": get_company_default(self.company, "cost_center"),
		}

		debit_gl_entry = frappe._dict(base_gl_entry).update({
			"party_type": self.party_type,
			"party": self.party,
			"account": self.party_account,
			"account_currency": frappe.get_value("Account", self.party_account, "account_currency"),
			"against": against,
			"debit": flt(amount) * flt(self.exchange_rate),
			"debit_in_account_currency": flt(amount),
		})

		credit_gl_entry = frappe._dict(base_gl_entry).update({
			"account": against,
			"account_currency": frappe.get_value("Account", against, "account_currency"),
			"against": self.party,
			"credit":  flt(amount) * flt(self.exchange_rate),
			"credit_in_account_currency": flt(amount),
		})
		
		return [debit_gl_entry, credit_gl_entry]

	def make_gl_entries(self, cancel=False, adv_adj=False):
		from erpnext.accounts.general_ledger import make_gl_entries

		# amount that was disbursed from the bank account
		lent_amount = self.get_lent_amount()

		gl_map = self.get_double_matched_entry(lent_amount, self.disbursement_account)
		gl_map += self.get_double_matched_entry(self.legal_expenses_amount, self.income_account)
		gl_map += self.get_double_matched_entry(self.total_interest_amount, self.income_account)

		make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, merge_entries=False)
	
	def is_elegible_for_deletion(self):
		if self.outstanding_amount == 0 \
			or self.paid_amount > 0: return False
		return True

def on_doctype_update():
	# let's drop the view if exists
	frappe.db.sql("""DROP VIEW IF EXISTS `viewPaid Fine`""")
	
	# let's create the view
	frappe.db.sql("""
		CREATE VIEW `viewPaid Fine` AS SELECT 
			loan.name as loan,
			loan.party as party,
			charge.repayment_period as repayment,
			(SELECT DATE(MAX(t.creation)) FROM `tabIncome Receipt Items` t WHERE t.voucher_name = charge.name) as fecha,
			charge.total_amount as paid_amount,
			charge.total_amount as total_amount,
			charge.loan_charges_type as type, 
			charge.status as status
		FROM 
			`tabLoan Charges` charge
		JOIN 
			`tabLoan` loan 
		ON 
			loan.name = charge.loan
		""")
