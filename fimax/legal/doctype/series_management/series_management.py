# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SeriesManagement(Document):
	def onload(self):
		series_list = frappe.db.sql_list("""SELECT
				name 
			FROM tabSeries""")

		self.set_onload("options", "\n".join(series_list))

	def get_current(self):
		if not self.serie: return

		result = frappe.db.sql_list("""SELECT
				current 
			FROM tabSeries
			WHERE name = %(serie)s""", 
		self.as_dict())

		if result:
			self.current = result[0]

	def update_series(self):
		if not self.serie: return

		self.validate_value("current", ">=", 0)

		frappe.db.sql("""UPDATE tabSeries
				SET current = %(current)s
			WHERE name = %(serie)s""", self.as_dict())

		frappe.msgprint("Updated")




