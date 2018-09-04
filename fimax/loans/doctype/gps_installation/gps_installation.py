# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import formatdate
from frappe.utils import flt, cint, cstr, nowdate
from frappe import _ as __

class GPSInstallation(Document):

	def on_submit(self):
		self.create_event()

	def create_event(self):
		event = frappe.new_doc("Event")
		event.subject = __("The GPS installation {} is due on {}".format(self.name, formatdate(self.ends_date)))
		event.starts_on = self.ends_date
		event.ends_on = "{} 23:59:59".format(cstr(self.ends_date)) 
		event.event_type = "Public"
		event.all_day = True
		event.insert(ignore_permissions=True)
