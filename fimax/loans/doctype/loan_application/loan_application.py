# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from fimax.api import create_loan_from_appl

class LoanApplication(Document):
	def validate(self):
		self.set_approved_amounts()
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

	def set_approved_amounts(self):
		if frappe.session.user == self.owner:
			self.approved_gross_amount = self.requested_gross_amount

	def validate_approved_amounts(self):
		if self.approved_gross_amount > self.requested_gross_amount:
			frappe.throw(__("Approved Amount can not be greater than Requested Amount"))