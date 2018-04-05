# -*- coding: utf-8 -*-
# Copyright (c) 2018, Yefri Tavarez and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

test_records = frappe.get_test_records('Loan Charges')

class TestLoanCharges(unittest.TestCase):
	def setUp(self):
		self.create_loan_charges_type()
		self.submit_loan_charges()

	def create_loan_charges_type(self):
		if not frappe.db.exists("Loan Charges Type", "_Life Insurance"):
			frappe.get_doc({
				'description': None,
				'doctype': 'Loan Charges Type',
				'loan_charges_name': "_Life Insurance",
				'repayment_frequency': 'Monthly',
				'repayment_periods': 1
			}).insert()

	def submit_loan_charges(self):
		for loan_charge in frappe.get_list("Loan Charges", {
			"docstatus": 0
		}):
			doc = frappe.get_doc("Loan Charges", loan_charge.name)
			# doc.submit()

	def test_status(self):
		status_list = [
			"Pending",
			"Pending",
			"Overdue",
			"Overdue",
			"Paid",
			"Paid",
			"Partially",
			"Overdue",
		]

		for index, record in enumerate(test_records):
			doc = frappe.copy_doc(record)
			doc.insert()

			doc.update_status()
			doc.submit()

			self.assertEquals(status_list[index], doc.status)
