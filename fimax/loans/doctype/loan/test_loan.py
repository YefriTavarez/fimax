# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

from fimax.api import create_loan_from_appl
from frappe.utils import flt, cint, cstr

test_records = frappe.get_test_records('Loan Application')

class TestLoan(unittest.TestCase):
	def setUp(self):
		self.create_loan()

	def tearDown(self):
		pass

	def create_loan(self):
		self.loan_appl = frappe.get_last_doc("Loan Application")
		self.interest_rate = 1.32

		loan = create_loan_from_appl(self.loan_appl)
		loan.mode_of_payment = "Cash"
		loan.party_account = frappe.get_value("Account", {
			"account_type": "Receivable"
		})

		loan.loan_application = pick_one_loan_appl()

		loan.insert()
		self.loan = loan

	def test_loan_totals(self):
		loan = self.loan
		self.assertEquals(round(loan.repayment_amount), 5462.00)
		self.assertEquals(loan.interest_rate, self.interest_rate)
		self.assertEquals(round(loan.legal_expenses_amount), 10500.00)
		self.assertEquals(round(loan.total_payable_amount), 262193.00)
		self.assertEquals(round(loan.total_interest_amount), 101693.00)
		self.assertEquals(round(loan.total_capital_amount), loan.loan_amount)

	def test_loan_schedule_dates(self):
		test_records = frappe.get_test_records('Loan')
		doc = frappe.get_doc(test_records[1])
		doc.loan_application = pick_one_loan_appl()
		doc.mode_of_payment = "Cash"
		doc.party_account = frappe.get_value("Account", {
			"account_type": "Receivable"
		})

		doc.submit()

		self.assertEquals(cstr(doc.loan_schedule[0].repayment_date), "2000-02-29")
		self.assertEquals(cstr(doc.loan_schedule[1].repayment_date), "2000-03-30")
		self.assertEquals(cstr(doc.loan_schedule[2].repayment_date), "2000-04-30")

def pick_one_loan_appl():
	return frappe.db.sql("""SELECT
			name
		FROM
			`tabLoan Application` 
		WHERE
			docstatus < 2 
			AND status != 'Rejected' 
			AND name NOT IN 
			(
				SELECT
					tabLoan.loan_application 
				FROM
					tabLoan 
				WHERE
					tabLoan.loan_application = `tabLoan Application`.name 
					AND tabLoan.docstatus < 2
			)""", 
	as_list=True)[0][0]
