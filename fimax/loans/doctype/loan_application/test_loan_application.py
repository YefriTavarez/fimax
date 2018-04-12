# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

test_records = frappe.get_test_records('Loan Application')

class TestLoanApplication(unittest.TestCase):
	def setUp(self):
		self.create_loan_type()
		self.create_loan_application()

	def tearDown(self):
		pass

	def create_loan_type(self):
		self.interest_rate = 1.32

		if not frappe.db.get_value("Custom Loan", "Home Loan"):
			frappe.get_doc({
				"asset_type": "",
				"currency": "DOP",
				"doctype": "Custom Loan",
				"enabled": 1,
				"interest_rate": self.interest_rate,
				"interest_type": "Simple",
				"legal_expenses_rate": 0,
				"loan_name": "Home Loan",
				"maximum_loan_amount": 1500000,
				"repayment_day_of_the_month": "30",
				"repayment_day_of_the_week": "2",
				"repayment_days_after_cutoff": "2",
				"repayment_frequency": "Daily"
			}).insert()

	def create_loan_application(self):
		self.loan_application = frappe.copy_doc(test_records[0])
		self.loan_application.status = "Approved"
		self.loan_application.submit()

	def test_loan_totals(self):
		loan_application = self.loan_application
		self.assertEquals(round(loan_application.repayment_amount), 5462.00)
		self.assertEquals(loan_application.interest_rate, self.interest_rate)
		self.assertEquals(loan_application.legal_expenses_amount, 10500.00)
