# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from fimax.api import rate_to_decimal as dec
from fimax.api import create_loan_from_appl

from fimax import simple
from fimax import compound

from frappe.utils import flt, cint, cstr
from frappe import _ as __

class Loan(Document):
	def validate(self):
		self.set_missing_values()
		self.update_repayment_schedule_dates()

	def before_insert(self):
		if not self.loan_application:
			frappe.throw(__("Missing Loan Application!"))

		self.validate_loan_application()

	def after_insert(self):
		pass

	def before_submit(self):
		pass

	def on_submit(self):
		self.commit_to_loan_charges()

	def before_cancel(self):
		self.rollback_from_loan_charges()

	def on_cancel(self):
		pass

	def on_trash(self):
		pass

	def make_loan(self):
		if self.loan_application:
			loan_appl = frappe.get_doc(self.meta.get_field("loan_application").options, 
				self.loan_application)

			self.evaluate_loan_application(loan_appl)

			return create_loan_from_appl(loan_appl)

	def set_missing_values(self):
		# simple or compound variable
		soc = simple
	
		if self.interest_type == "Compound":
			soc = compound

		self.total_capital_amount = self.loan_amount

		self.repayment_amount = soc.get_repayment_amount(self.total_capital_amount, 
			dec(self.interest_rate), self.repayment_periods)

		self.total_interest_amount = soc.get_total_interest_amount(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods)

		self.total_payable_amount = soc.get_total_payable_amount(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods)

		# empty the table to avoid duplicated rows
		self.set("loan_schedule", [])

		for row in soc.get_as_array(self.total_capital_amount,
			dec(self.interest_rate), self.repayment_periods):

			repayment_date = frappe.utils.add_months(self.posting_date, row.idx)
			
			row.update({
				"status": "Pending",
				"repayment_date": self.get_correct_date(repayment_date),
				"outstanding_amount": row.repayment_amount,
				"paid_amount": 0.000
			})

			self.append("loan_schedule", row)

	def get_correct_date(self, repayment_date):
		last_day_of_the_month = frappe.utils.get_last_day(repayment_date)
		first_day_of_the_month = frappe.utils.get_first_day(repayment_date)

		if cint(self.repayment_day_of_the_month) > last_day_of_the_month.day:
			return last_day_of_the_month.replace(last_day_of_the_month.year, 
				last_day_of_the_month.month, last_day_of_the_month.day)
		else:
			return frappe.utils.add_days(first_day_of_the_month, 
				cint(self.repayment_day_of_the_month) - 1)

	def update_repayment_schedule_dates(self):
		for row in self.loan_schedule:
			row.repayment_date = self.get_correct_date(row.repayment_date) 

	def validate_loan_application(self):
		if self.loan_application:
			loan_appl = frappe.get_doc(self.meta.get_field("loan_application").options, 
				self.loan_application)

			self.evaluate_loan_application(loan_appl)

	def evaluate_loan_application(self, loan_appl):
		if loan_appl.docstatus == 0:
			frappe.throw(__("Submit this Loan Application first!"))

		elif loan_appl.docstatus == 2:
			frappe.throw(__("The selected Loan Application is already cancelled!"))

		if frappe.db.exists("Loan", { 
			"loan_application": loan_appl.name ,
			"docstatus": ["!=", "2"]
		}):
			frappe.throw(__("The selected Loan Application already has a Loan document attached to it!"))

			
	def commit_to_loan_charges(self):
		from fimax.install import add_default_loan_charges_type
		
		# run this to make sure default loan charges type are set
		add_default_loan_charges_type()

		for row in self.loan_schedule:
			capital_loan_charge = row.get_new_loan_charge("Capital", row.capital_amount)
			capital_loan_charge.submit()

			interest_loan_charge = row.get_new_loan_charge("Interest", row.interest_amount)
			interest_loan_charge.submit()

	def rollback_from_loan_charges(self):
		for row in self.loan_schedule:
			[self.cancel_and_delete_loan_charge(row, lct) 
				for lct in ('Capital', 'Interest')]

	def cancel_and_delete_loan_charge(self, child, loan_charge_type):
		capital_loan_charge = child.get_loan_charge(loan_charge_type)

		fimax.utils.delete_doc(capital_loan_charge)		

		frappe.db.commit()
