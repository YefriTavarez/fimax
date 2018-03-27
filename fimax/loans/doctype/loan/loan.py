# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from fimax.api import rate_to_decimal as dec
from fimax import simple
from fimax import compound

from frappe.utils import add_months

class Loan(Document):
	def validate(self):
		self.set_missing_values()

	def before_insert(self):
		frappe.msgprint("before_insert")

	def after_insert(self):
		frappe.msgprint("after_insert")

	def before_submit(self):
		frappe.msgprint("before_submit")

	def on_submit(self):
		frappe.msgprint("on_submit")

	def before_cancel(self):
		frappe.msgprint("before_cancel")

	def on_cancel(self):
		frappe.msgprint("on_cancel")

	def on_trash(self):
		frappe.msgprint("on_trash")

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


