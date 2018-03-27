# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe import _ as __
from fimax.api import create_loan_from_appl
from fimax.api import rate_to_decimal as dec

from fimax import simple, compound


class LoanApplication(Document):
	def validate(self):
		self.set_missing_values()
		self.set_approved_amounts()
		self.validate_approved_amounts()
		self.set_repayment_amount()

	def on_update_after_submit(self):
		self.validate_approved_amounts()

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
		return create_loan_from_appl(self)

	def set_missing_values(self):
		if not self.posting_date:
			self.posting_date = frappe.utils.nowdate()

	def set_approved_amounts(self):
		if frappe.session.user == self.owner:
			self.approved_gross_amount = self.requested_gross_amount

	def validate_approved_amounts(self):
		if self.approved_gross_amount > self.requested_gross_amount:
			frappe.throw(__("Approved Amount can not be greater than Requested Amount"))

	def validate_required_fields_for_repayment_amount(self):
		if not self.approved_net_amount:
			frappe.throw(__("Missing Approved Net Amount"))

		if not self.interest_rate:
			frappe.throw(__("Missing Interest Rate"))

		if not self.repayment_periods:
			frappe.throw(__("Missing Repayment Periods"))

	def set_repayment_amount(self):
		# simple or compound variable
		soc = simple

		self.validate_required_fields_for_repayment_amount()
	
		if self.interest_type == "Compound":
			soc = compound

		self.repayment_amount = soc.get_repayment_amount(self.approved_net_amount, 
			dec(self.interest_rate), self.repayment_periods)
