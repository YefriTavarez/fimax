# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from fimax.simple import get_monthly_repayment_amount
from fimax.api import rate_to_decimal as dec

class Loan(Document):
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
		self.monthly_repayment_amount = get_monthly_repayment_amount(self.loan_amount, 
			dec(self.interest_rate), self.repayment_periods)