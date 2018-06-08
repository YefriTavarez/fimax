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

	def on_submit(self):
		pass

	def on_cancel(self):
		pass

	def update_status(self):
		pass	
		# No se me va a olvidar

	def before_cancel(self):
		self.status = "Cancelled"

	def set_missing_and_default_values(self):
		self.set_missing_values()
		self.set_default_values()

	def set_missing_values(self):
		self.insurance_supplier = frappe.db.get_single_value("Control Panel",
			"insurance_supplier")

	def set_default_values(self):
		self.repayment_periods = frappe.db.get_single_value("Control Panel",
			"repayment_periods")
	
	def commit_to_loan_charges(self):
		from fimax.install import add_default_loan_charges_type
		
		# run this to make sure default loan charges type are set
		add_default_loan_charges_type()

		for repayment in self.insurance_repayment_schedule:
			lc = row.get_new_loan_charge([("Insurance", repayment.repayment_amount)])
			lc.currency = self.currency
			lc.submit()
