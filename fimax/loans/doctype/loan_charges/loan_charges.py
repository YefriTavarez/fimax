# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr, nowdate
from frappe import _ as __

class LoanCharges(Document):
	def validate(self):
		pass

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
