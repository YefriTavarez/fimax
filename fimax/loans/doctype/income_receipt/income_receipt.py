# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on
from erpnext.setup.utils import get_exchange_rate

from frappe.utils import flt, cstr, cint

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

		self.exchange_rate = get_exchange_rate(loan_doc.currency, self.income_account_currency)
		self.currency = frappe.get_value("Company", self.company, "default_currency")
		
		for charge in self.list_loan_charges():
			self.append("income_receipt_items", 
				self.get_income_receipt_item(loan_doc, charge))

		
		self.grand_total = sum([row.base_total_amount for row in self.income_receipt_items])
		self.total_outstanding = sum([row.base_outstanding_amount for row in self.income_receipt_items])
		self.total_paid = self.total_outstanding

		self.difference_amount = 0.000

	def get_income_receipt_item(self, loan_doc, charge_doc):
		against_account_currency = frappe.get_value("Account", self.income_account, "account_currency")

		party_exchange_rate = get_exchange_rate(loan_doc.currency, self.currency)
		against_exchange_rate = get_exchange_rate(against_account_currency, self.currency)

		return frappe._dict({
			"account": loan_doc.party_account,
			"repayment_period": charge_doc.repayment_period,
			"loan_charges_type": charge_doc.loan_charges_type,
			"account_currency": loan_doc.currency,
			"against_account": self.income_account,
			"against_account_currency": against_account_currency,
			"outstanding_amount": charge_doc.outstanding_amount,
			"base_outstanding_amount": charge_doc.outstanding_amount * party_exchange_rate,
			"allocated_amount": charge_doc.outstanding_amount * party_exchange_rate / against_exchange_rate,
			"base_allocated_amount": charge_doc.outstanding_amount * party_exchange_rate / against_exchange_rate * against_exchange_rate,
			"total_amount": charge_doc.total_amount,
			"base_total_amount": charge_doc.total_amount * party_exchange_rate,
			"against_exchange_rate": against_exchange_rate,
			"party_exchange_rate": party_exchange_rate,
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
