# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Property(Document):
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
