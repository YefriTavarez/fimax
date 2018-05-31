# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr

class InsuranceCard(Document):
	def validate(self):
		loan_repayment_periods = frappe.get_value("Loan", 
			self.loan, "repayment_periods")

		self.validate_value("repayment_periods", "<=", cint(loan_repayment_periods))

	def set_missing_and_default_values(self):
		self.set_missing_values()
		self.set_default_values()

	def set_missing_values(self):
		pass
	
	def set_default_values(self):
		self.repayment_periods, self.insurance_supplier = [frappe.db.get_single_value("Control Panel", f) for 
			f in ['repayment_periods', 'insurance_supplier']]
