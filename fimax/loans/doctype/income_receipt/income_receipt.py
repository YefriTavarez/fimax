# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on
from erpnext.setup.utils import get_exchange_rate

class IncomeReceipt(Document):
	def list_loan_charges(self):
		fields = [
			"name",
			"outstanding_amount",
			"total_amount",
			"reference_type",
			"reference_name",
			"repayment_period",
			"loan_charges_type"
		]

		filters = {
			'loan': ['=', self.loan],
			'repayment_date': ['<=', self.posting_date],
			'status': ['not in', 'Paid, Closed'],
		}

		return frappe.get_list("Loan Charges", filters=filters, fields=fields, order_by='name')

	def grab_loan_charges(self):
		# empty the table first
		self.set("income_receipt_items", [])
		
		loan_doc = frappe.get_doc("Loan", self.loan)
		self.income_account, self.income_account_currency = self.get_income_account_and_currency(loan_doc)

		self.exchange_rate = get_exchange_rate(self.income_account_currency, loan_doc.currency)

		for charge in self.list_loan_charges():
			self.append("income_receipt_items", 
				self.get_income_receipt_item(loan_doc, charge))

			self.grand_total += charge.total_amount
			self.total_outstanding += charge.outstanding_amount
			self.total_paid += charge.outstanding_amount
		
		self.difference_amount = 0.000

	def get_income_receipt_item(self, loan_doc, charge_doc):
		return frappe._dict({
			"account": loan_doc.party_account,
			"repayment_period": charge_doc.repayment_period,
			"loan_charges_type": charge_doc.loan_charges_type,
			"account_currency": loan_doc.currency,
			"against_account": self.income_account,
			"against_account_currency": frappe.get_value("Account", self.income_account, "account_currency"),
			"outstanding_amount": charge_doc.outstanding_amount,
			"allocated_amount": charge_doc.outstanding_amount,
			"allocated_amount_in_account_currency": charge_doc.outstanding_amount,
			"total_amount": charge_doc.total_amount,
			"exchange_rate": self.exchange_rate,
			"reference_type": charge_doc.reference_type,
			"reference_name": charge_doc.reference_name,
			"voucher_type": "Loan Charges",
			"voucher_name": charge_doc.name,
		})

	def get_income_account_and_currency(self, loan_doc):

		income_account = frappe.get_value("Mode of Payment Account", filters={
			"parent": loan_doc.mode_of_payment,
			"company": loan_doc.company
		}, fieldname=["default_account"])

		account_currency = frappe.get_value("Account", income_account, "account_currency")

		return (income_account, account_currency)
