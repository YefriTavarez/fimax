# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr, nowdate

class LoanRepaymentSchedule(Document):
	def autoname(self):
		self.name = "{0}-NO-{1}".format(self.parent, self.idx)

	def update_status(self):

		# it's pending if repayment date is in the future and has nothing paid
		if cstr(self.repayment_date) >= nowdate() and self.paid_amount == 0.000:
			self.status = "Pending"

		# it's partially paid if repayment date is in the future and has something paid
		if cstr(self.repayment_date) > nowdate() and self.paid_amount > 0.000:
			self.status = "Partially"

		# it's overdue if repayment date is in the past and is not fully paid
		if cstr(self.repayment_date) < nowdate() and self.outstanding_amount > 0.000:
			self.status = "Overdue"

		# it's paid if paid and total amount are equal hence there's not outstanding amount
		if self.paid_amount == self.repayment_amount:
			self.status = "Paid"


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
		filters_dict = {
			'loan_charges_type': loan_charges_type,
			'repayment_date': cstr(self.repayment_date),
			'loan': self.parent,
			'reference_type': self.doctype,
			'reference_name': self.name,
		}

		if frappe.db.exists("Loan Charges", filters_dict):
			return frappe.get_doc("Loan Charges", filters_dict)
