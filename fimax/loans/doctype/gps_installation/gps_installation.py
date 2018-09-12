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
	def validate(self):
		loan_repayment_periods = frappe.get_value("Loan", 
			self.loan, "repayment_periods")

		self.validate_value("repayment_periods", "<=", cint(loan_repayment_periods))	

	def on_submit(self):
		self.commit_to_loan_charges()
		self.create_event()

	def create_event(self):
		event = frappe.new_doc("Event")
		event.subject = __("The GPS installation {} is due on {}".format(self.name, formatdate(self.end_date)))
		event.starts_on = self.end_date
		event.ends_on = "{} 23:59:59".format(cstr(self.end_date)) 
		event.event_type = "Public"
		event.all_day = True

		event.insert(ignore_permissions=True)

	def on_cancel(self):
		self.status = "Cancelled"

	def update_status(self):
		pass	

	def before_submit(self):
		if self.start_date <= nowdate() and nowdate() <= self.end_date:
			self.status = "Active"
		else:
			self.status = "Inactive"

	def before_cancel(self):
		self.rollback_from_loan_charges()

	def set_missing_and_default_values(self):
		self.set_missing_values()
		self.set_default_values()

	def set_missing_values(self):
		self.gps_supplier = frappe.db.get_single_value("Control Panel",
			"gps_supplier")

	def set_default_values(self):
		self.repayment_periods = frappe.db.get_single_value("Control Panel",
			"gps_repayment_periods")
	
	def commit_to_loan_charges(self):
		from fimax.install import add_default_loan_charges_type
		
		# run this to make sure default loan charges type are set
		add_default_loan_charges_type()

		if self.initial_payment_amount > 0.000:
			self.setup_initial_payment()
			

		for row in self.gps_repayment_schedule:
			loan_charges = row.get_new_loan_charge("GPS", row.repayment_amount)
			loan_charges.currency = self.currency

			loan_charges.update_status()
			
			# insert the record
			loan_charges.insert()

			# finally submit
			loan_charges.submit()

	def rollback_from_loan_charges(self):
		if self.initial_payment_amount > 0.000:
			self.rollback_initial_payment()

		for row in self.gps_repayment_schedule:
			self.cancel_and_delete_loan_charge(row, "GPS")

	def cancel_and_delete_loan_charge(self, child, loan_charge_type):
		loan_charge = child.get_loan_charge(loan_charge_type)

		if not loan_charge or not loan_charge.name: return
		
		doc = frappe.get_doc("Loan Charges", loan_charge.name)
		
		self.validate_and_delete_loan_charge(doc)

	def validate_and_delete_loan_charge(self, doc):
		import fimax.utils

		if not doc.status in ("Overdue", "Pending"):
			frappe.throw(__("Could not cancel GPS Installation because Loan Charge {}:{} is not Pending anymore!"
				.format(doc.name, doc.loan_charge_type)))

		fimax.utils.delete_doc(doc)

		frappe.db.commit()

	def setup_initial_payment(self):
		loan_charges = frappe.get_doc({
			'doctype': 'Loan Charges',
			'loan_charges_type': "GPS",
			'outstanding_amount': self.initial_payment_amount,
			'paid_amount': 0.000,
			'reference_type': self.doctype,
			'reference_name': self.name,
			'loan': self.loan,
			'repayment_date': cstr(self.start_date),
			'status': 'Overdue',
			'repayment_period': self.get_current_repayment_period(),
			'total_amount': self.initial_payment_amount
		})

		loan_charges.currency = self.currency
		loan_charges.submit()

	def rollback_initial_payment(self):
		filters_dict = {
			'loan_charges_type': "GPS",
			'repayment_date': cstr(self.start_date),
			'loan': self.loan,
			'reference_type': self.doctype,
			'reference_name': self.name,
		}

		if frappe.db.exists("Loan Charges", filters_dict):
			doc = frappe.get_doc("Loan Charges", filters_dict)
			self.validate_and_delete_loan_charge(doc)

	def get_current_repayment_period(self):
		return frappe.get_value("Loan Repayment Schedule", {
			"parent": self.loan,
			"parenttype": "Loan",
			"parentfield": "loan_schedule",
			"status": ["not in", ["Closed", "Paid"]]
		}, ["idx"], order_by="idx") or 1

	def sync_this_with_loan_charges(self):
		records = len(self.gps_repayment_schedule) or 1

		for idx, row in enumerate(self.gps_repayment_schedule):
			self.publish_realtime(idx + 1, records)

			paid_amount, last_status = frappe.db.get_value("Loan Charges", filters={
				"docstatus": 1,
				"status": ["!=", "Closed"],
				"reference_type": row.doctype,
				"reference_name": row.name,
			}, fieldname=[
				"SUM(paid_amount)",
				"status"], order_by="name ASC")

			row.paid_amount = flt(paid_amount)
			row.outstanding_amount = flt(row.repayment_amount - row.paid_amount)
			row.status = last_status or row.status
			row.submit()

	def publish_realtime(self, current, total):
		frappe.publish_realtime("real_progress", {
			"progress": flt(current) / flt(total) * 100, 
		}, user=frappe.session.user)
