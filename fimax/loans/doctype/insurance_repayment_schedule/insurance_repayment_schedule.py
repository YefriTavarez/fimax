# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class InsuranceRepaymentSchedule(Document):
	
	def rename(self):
		new_name = "{0}-NO-{1}".format(self.parent, self.idx)
		frappe.rename_doc(self.doctype, self.name, new_name, force=True)

	def get_new_loan_charge(self, loan_charges_type, amount):
		insurance_card = frappe.get_doc(self.parenttype, self.parent)

		return frappe.get_doc({
			'doctype': 'Loan Charges',
			'loan_charges_type': loan_charges_type,
			'outstanding_amount': amount,
			'paid_amount': 0.000,
			'reference_type': self.doctype,
			'reference_name': self.name,
			'loan': insurance_card.loan,
			'repayment_date': self.repayment_date,
			'status': 'Pending',
			'repayment_period': self.idx,
			'total_amount': amount
		})

	def get_loan_charge(self, loan_charges_type):
		insurance_card = frappe.get_doc(self.parenttype, self.parent)
		
		filters_dict = {
			'loan_charges_type': loan_charges_type,
			'repayment_date': cstr(self.repayment_date),
			'loan': insurance_card.loan,
			'reference_type': self.doctype,
			'reference_name': self.name,
		}

		return frappe.get_all("Loan Charges", filters_dict)
