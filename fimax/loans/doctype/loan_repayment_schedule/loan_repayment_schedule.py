# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr

class LoanRepaymentSchedule(Document):
	def autoname(self):
		self.name = "{0}-NO-{1}".format(self.parent, self.idx)

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
			'repayment_date': cstr(self.repayment_date),
			'loan': self.parent,
			'reference_type': self.doctype,
			'reference_name': self.name,
			'loan_charges_type': loan_charges_type
		}

		if frappe.db.exists("Loan Charges", filters_dict):
			return frappe.get_doc("Loan Charges", filters_dict)
