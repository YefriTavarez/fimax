# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class LoanRepaymentSchedule(Document):
	def get_new_loan_charge(self, loan_charges_type, amount):
		return frappe.get_doc({
			'amount': amount,
			'doctype': 'Loan Charges',
			'loan_charges_type': loan_charges_type,
			'outstanding_amount': amount,
			'paid_amount': 0.000,
			'reference_type': self.doctype,
			'reference_name': self.name,
			'loan': self.parent,
			'repayment_date': self.repayment_date,
			'status': 'Pending',
			'total_amount': amount
		})

	def get_loan_charge(self, loan_charges_type):
		return frappe.get_doc("Loan Charge", {
			'repayment_date': self.repayment_date,
			'loan': self.parent,
			'reference_type': self.doctype,
			'reference_name': self.name,
			'loan_charges_type': loan_charges_type,
		})