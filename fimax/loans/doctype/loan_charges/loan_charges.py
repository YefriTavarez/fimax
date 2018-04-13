# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt, cint, cstr, nowdate
from frappe import _ as __

from fimax.utils import DocStatus

class LoanCharges(Document):
	def validate(self):
		self.validate_amounts()
		self.set_missing_values()

	def before_insert(self):
		pass

	def after_insert(self):
		pass

	def before_submit(self):
		pass

	def on_submit(self):
		self.update_outstanding_amount()

	def before_cancel(self):
		pass

	def on_cancel(self):
		pass

	def on_trash(self):
		pass

	def set_missing_values(self):
		self.total_amount = flt(self.amount)
		self.outstanding_amount = self.total_amount

	def update_outstanding_amount(self):
		if not self.docstatus == 1.000:
			frappe.throw(__("Please submit this Loan Charge before updating the outstanding amount!"))
			
		outstanding_amount = flt(self.total_amount) - flt(self.paid_amount)

		if outstanding_amount < 0.000:
			frappe.throw(__("Outstanding amount cannot be negative!"))

		self.outstanding_amount = outstanding_amount
			

	def validate_reference_name(self):
		if not self.loan:
			frappe.throw(__("Missing Loan!"))

		if not self.reference_type:
			frappe.throw(__("Missing Repayment Type!"))

		if not self.reference_name:
			frappe.throw(__("Missing Repayment Name!"))

		docstatus = frappe.db.get_value(self.reference_type, 
			self.reference_name, "docstatus")

		if DocStatus(docstatus) is not DocStatus.SUBMITTED:
			frappe.throw(__("Selected {0} is not submitted!".format(self.reference_type)))


	def validate_amounts(self):
		if not flt(self.amount):
			frappe.throw(__("Missing amount!"))

		if flt(self.paid_amount) > flt(self.total_amount):
			frappe.throw(__("Paid Amount cannot be greater than Total amount!"))
			

	def update_status(self):

		# it's pending if repayment date is in the future and has nothing paid
		if cstr(self.repayment_date) >= nowdate() and self.paid_amount == 0.000:
			self.status = "Pending"

		# it's partially paid if repayment date is in the future and has something paid
		if cstr(self.repayment_date) > nowdate() and self.paid_amount > 0.000:
			self.status = "Partially"

		# it's overdue if repayment date is in the past and is not fully paid
		if cstr(self.repayment_date) < nowdate() and self.outstanding_amount > 0.000:
			self.status = "Overdue"

		# it's paid if paid and total amount are equal hence there's not outstanding amount
		if self.paid_amount == self.total_amount:
			self.status = "Paid"
