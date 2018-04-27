# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on

class IncomeReceipt(Document):
	def list_loan_charges(self):
		return frappe.db.sql("""SELECT
			name,
			outstanding_amount,
			total_amount,
			reference_type,
			reference_name 
		FROM
			`tabLoan Charges` 
		WHERE
			loan = %(loan)s 
			AND repayment_date <= %(posting_date)s 
			AND 
			(
				status != "Paid" 
				OR status = "Overdue"
			)""", self.as_dict(), as_dict=True)

	def grab_loan_charges(self):
		self.set("income_receipt_items", [])
		
		for charge in self.list_loan_charges():
			loan_doc = frappe.get_doc("Loan", self.loan)
			against_account = frappe.get_value("Mode of Payment Account", filters={
				"parent": loan_doc.mode_of_payment,
				"company": loan_doc.company
			}, fieldname=["default_account"])

			self.append("income_receipt_items", {
				"account": loan_doc.party_account,
				"account_currency": loan_doc.currency,
				"against_account": against_account,
				"against_account_currency": frappe.get_value("Account", against_account, "account_currency"),
				"outstanding_amount": charge.outstanding_amount,
				"allocated_amount": charge.outstanding_amount,
				"allocated_amount_in_account_currency": charge.outstanding_amount,
				"total_amount": charge.total_amount,
				"exchange_rate": 1.0,
				"reference_type": charge.reference_type,
				"reference_name": charge.reference_name,
				"voucher_type": "Loan Charges",
				"voucher_name": charge.name,
			})

			self.grand_total += charge.total_amount
			self.total_outstanding += charge.outstanding_amount
			self.total_paid += charge.outstanding_amount
			self.difference_amount = 0.000
