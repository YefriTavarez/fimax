# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr, nowdate

class InsuranceRepaymentSchedule(Document):
	
	def rename(self):
		new_name = "{0}-NO-{1}".format(self.parent, self.idx)
		frappe.rename_doc(self.doctype, self.name, new_name, force=True)

	def get_new_loan_charge(self, loan_charges_type, amount):
		loan = frappe.get_value(self.parenttype, self.parent, "loan")

		return frappe.get_doc({
			'doctype': 'Loan Charges',
			'loan_charges_type': loan_charges_type,
			'outstanding_amount': amount,
			'paid_amount': 0.000,
			'reference_type': self.doctype,
			'reference_name': self.name,
			'loan': loan,
			'repayment_date': cstr(self.repayment_date),
			'status': 'Pending',
			'repayment_period': self.idx,
			'total_amount': amount
		})

	def get_loan_charge(self, loan_charges_type):
		loan = frappe.get_value(self.parenttype, self.parent, "loan")
		
		filters_dict = {
			'loan_charges_type': loan_charges_type,
			'repayment_date': cstr(self.repayment_date),
			'loan': loan,
			'reference_type': self.doctype,
			'reference_name': self.name,
		}

		if frappe.db.exists("Loan Charges", filters_dict):
			return frappe.get_doc("Loan Charges", filters_dict)
