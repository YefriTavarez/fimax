# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ControlPanel(Document):
	def validate(self):
		self.validate_value("insurance_repayment_periods", ">", 0)
		self.validate_value("gps_repayment_periods", ">", 0)
