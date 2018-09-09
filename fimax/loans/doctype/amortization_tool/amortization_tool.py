# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from fimax.api import rate_to_decimal as dec
from fimax import simple, compound
from frappe.utils import flt, cint, cstr, nowdate
from fimax.utils import daily, weekly, biweekly, monthly, quartely, half_yearly, yearly
from frappe import _ as __

class AmortizationTool(Document):
	def validate(self):
		self.set_repayment_amount()

	def onload(self):
		self.make_repayment_schedule()

	def before_print(self):
		self.make_print_schedule()
	
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

		self.total_capital_amount = self.requested_net_amount

		self.total_interest_amount = soc.get_total_interest_amount(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods)

		self.total_payable_amount = soc.get_total_payable_amount(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods)
		
		self.make_repayment_schedule()

	def make_print_schedule(self):
		rows = self.get_repayment_schedule()
		
		self.amortization_schedule = frappe.render_template(
			"templates/repayment_schedule_print.html", {
				"rows": rows
			}
		)

	def get_repayment_schedule(self):
		if not self.approved_net_amount \
			or not self.repayment_periods \
			or not self.interest_rate: return

		soc = simple
		
		if self.interest_type == "Compound":
			soc = compound

		self.repayment_amount = soc.get_repayment_amount(self.approved_net_amount, 
			dec(self.interest_rate), self.repayment_periods)

		self.total_capital_amount = self.requested_net_amount
		
		rows = soc.get_as_array(self.total_capital_amount, 
			dec(self.interest_rate), self.repayment_periods)

		for row in rows:
			repayment_date = frappe._dict({
				"Daily": daily,
				"Weekly": weekly,
				"BiWeekly": biweekly,
				"Monthly": monthly,
				"Quartely": quartely,
				"Half-Yearly": half_yearly,
				"Yearly": yearly
			}).get(self.repayment_frequency)(self.disbursement_date, row.idx)

			row.update({
				"repayment_date": frappe.format_value(repayment_date, df={"fieldtype": "Date"})
			})

		return rows

	def make_repayment_schedule(self):
		rows = self.get_repayment_schedule()

		self.amortization_schedule = frappe.render_template(
			"templates/repayment_schedule_form.html", {
				"rows": rows
			}
		)
