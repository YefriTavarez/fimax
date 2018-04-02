# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from fimax.api import rate_to_decimal as dec
from fimax.api import create_loan_from_appl

from fimax import simple
from fimax import compound

from frappe.utils import add_months
from frappe import _ as __

class Loan(Document):
	def validate(self):
		self.set_missing_values()

	def before_insert(self):
		pass

	def after_insert(self):
		pass

	def before_submit(self):
		pass

	def on_submit(self):
		pass

	def before_cancel(self):
		pass

	def on_cancel(self):
		pass

	def on_trash(self):
		pass

	def make_loan(self):
		if self.loan_application:
			loan_appl = frappe.get_doc(self.meta.get_field("loan_application").options, 
				self.loan_application)

			self.evaluate_loan_application(loan_appl)

			return create_loan_from_appl(loan_appl)

	def set_missing_values(self):
		# simple or compound variable
		soc = simple
	
		if self.interest_type == "Compound":
			soc = compound

		self.total_capital_amount = self.loan_amount

		self.repayment_amount = soc.get_repayment_amount(self.total_capital_amount, 
			dec(self.interest_rate), self.repayment_periods)

		self.total_interest_amount = soc.get_total_interest_amount(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods)

		self.total_payable_amount = soc.get_total_payable_amount(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods)

		# empty the table to avoid duplicated rows
		self.set("loan_schedule", [])

		for row in soc.get_as_array(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods):
			
			row.update({
				"status": "Pending",
				"repayment_date": add_months(self.posting_date, row.idx),
				"outstanding_amount": row.repayment_amount,
				"paid_amount": 0.000
			})

			self.append("loan_schedule", row)

	def evaluate_loan_application(self, loan_appl):
		if loan_appl.docstatus == 0:
			frappe.throw(__("Submit this Loan Application first!"))

		elif loan_appl.docstatus == 2:
			frappe.throw(__("The selected Loan Application is already cancelled!"))

		if frappe.db.exists("Loan", { 
			"loan_application": loan_appl.name ,
			"docstatus": ["!=", "2"]
		}):
			frappe.throw(__("The selected Loan Application already has Loan document attached to it!"))


