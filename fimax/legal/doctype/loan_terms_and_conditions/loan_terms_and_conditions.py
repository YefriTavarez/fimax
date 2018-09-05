# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class LoanTermsandConditions(Document):
	def autoname(self):
		self.name = "{0}-{1}".format(self.loan, 
			self.terms_template)

	def get_terms_and_conditions(self):
		template = frappe.get_value(self.meta.get_field("terms_template").options, 
			self.terms_template, "terms")

		doc = frappe.get_doc(self.meta.get_field("loan").options,
			self.loan)

		self.terms_and_conditions = frappe.render_template(template, doc.as_dict())
