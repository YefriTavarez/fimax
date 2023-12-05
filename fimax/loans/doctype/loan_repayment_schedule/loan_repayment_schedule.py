# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr, nowdate
from frappe import _

class LoanRepaymentSchedule(Document):
	def autoname(self):
		self.name = "{0}-NO-{1}".format(self.parent, self.idx)

	def validate(self):
		self.update_status()

	def update_status(self):

		# it's pending if repayment date is in the future and has nothing paid
		if cstr(self.repayment_date) >= nowdate() and self.outstanding_amount > 0.000:
			self.status = "Pending"

			# it's overdue if repayment date is in the past and is not fully paid
		if cstr(self.repayment_date) <= nowdate() and self.outstanding_amount > 0.000:
			self.status = "Overdue"

		# it's partially paid if repayment date is in the future and has something paid
		if cstr(self.repayment_date) > nowdate() and self.paid_amount > 0.000:
			self.status = "Partially"
		
	
		# it's paid if paid and total amount are equal hence there's not outstanding amount
		if flt(self.paid_amount, 2) == flt(self.repayment_amount, 2)\
			or not flt(self.outstanding_amount, 0):
			self.status = "Paid"

	def validate_amounts(self):
		if not flt(self.repayment_amount):
			frappe.throw(_("Missing amount!"))

		if flt(self.paid_amount, 2) > flt(self.repayment_amount, 2):
			frappe.throw(_("Paid Amount cannot be greater than Total amount!"))

		if flt(self.outstanding_amount) < 0.000:
			frappe.throw(_("Outstanding Amount cannot be less than zero!"))

	def get_new_loan_charge(self, loan_charges_type, amount):
		return frappe.get_doc({
			'doctype': 'Loan Charges',
			'loan_charges_type': loan_charges_type,
			'outstanding_amount': amount,
			'paid_amount': 0.000,
			'reference_type': self.doctype,
			'reference_name': self.name,
			'loan': self.parent,
			'repayment_date': self.repayment_date,
			'status': 'Pending',
			'repayment_period': self.idx,
			'total_amount': amount
		})

	def get_loan_charge(self, loan_charges_type):
		doctype = "Loan Charges"

		filters_dict = {
			'loan_charges_type': loan_charges_type,
			'repayment_date': cstr(self.repayment_date),
			'loan': self.parent,
			'reference_type': self.doctype,
			'reference_name': self.name,
		}

		if frappe.db.exists(doctype, filters_dict):
			return frappe.get_doc(doctype, filters_dict)

	def set_pending_fine(self, amount=0.000):
		self.fine_amount = self.get_pending_fine()

		if amount:
			self.fine_amount = amount

	def get_pending_fine(self):
		result = frappe.db.sql("""SELECT
				SUM(total_amount) - SUM(paid_amount) AS pending_fine
			FROM `tabLoan Charges` 
			WHERE loan_charges_type = 'Late Payment Fee'
				AND status not in ('Closed', 'Paid')
				AND reference_type = %s
				AND reference_name = %s
			""", (self.doctype, self.name), as_list=True)

		if result:
			result = result[0][0]

		return frappe.utils.flt(result)
