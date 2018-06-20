# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on
from erpnext.setup.utils import get_exchange_rate

from frappe.utils import flt, cstr, cint, nowdate
from frappe import _

class IncomeReceipt(Document):
	def validate(self):
		self.validate_income_receipt_items()

	def on_submit(self):
		self.make_gl_entries(cancel=False)
		self.update_loan_charges(cancel=False)

	def on_cancel(self):
		self.make_gl_entries(cancel=True)
		self.update_loan_charges(cancel=True)
		
	def list_loan_charges(self, loan_charges_list=None):
		fields = [
			"name",
			"outstanding_amount",
			"total_amount",
			"reference_type",
			"reference_name",
			"repayment_period",
			"repayment_date",
			"status",
			"loan_charges_type"
		]

		filters = {
			'loan': ['=', self.loan],
			'repayment_date': ['<=', self.posting_date],
			'status': ['not in', 'Paid, Closed'],
		}

		if loan_charges_list:
			filters = {
				"name": ["in", loan_charges_list]
			}

		return frappe.get_list("Loan Charges", filters=filters, fields=fields, order_by='name')

	def grab_loan_charges(self, new_table=False, loan_charges_list=None):
		if new_table or not self.get("income_receipt_items") \
			or not self.get("income_receipt_items")[0].loan_charges_type:
			# empty the table first
			self.set("income_receipt_items", [])

		loan_doc = frappe.get_doc(self.meta.get_field("loan").options, self.loan)
		self.income_account, self.income_account_currency = self.get_income_account_and_currency(loan_doc)

		self.exchange_rate = get_exchange_rate(loan_doc.currency, self.income_account_currency)
		self.currency = frappe.get_value("Company", self.company, "default_currency")
		
		for charge in self.list_loan_charges(loan_charges_list):
			loan_charge = self.get_income_receipt_item(loan_doc, charge)

			# skip for duplicates
			if not loan_charge.get("voucher_name") in [d.get("voucher_name") 
				for d in self.income_receipt_items]: self.append("income_receipt_items", loan_charge)

		self.grand_total = sum([row.base_total_amount for row in self.income_receipt_items])
		self.total_outstanding = sum([row.base_outstanding_amount for row in self.income_receipt_items])
		self.total_paid = self.total_outstanding

		self.difference_amount = 0.000

	def get_income_receipt_item(self, loan_doc, charge_doc):
		self.income_account_currency = frappe.get_value("Account", self.income_account, "account_currency")

		party_exchange_rate = get_exchange_rate(loan_doc.currency, self.currency)
		against_exchange_rate = get_exchange_rate(self.income_account_currency, self.currency)

		return frappe._dict({
			"account": loan_doc.party_account,
			"repayment_period": charge_doc.repayment_period,
			"repayment_date": charge_doc.repayment_date,
			"status": charge_doc.status,
			"loan_charges_type": charge_doc.loan_charges_type,
			"account_currency": loan_doc.currency,
			"mode_of_payment": loan_doc.mode_of_payment,
			"against_account": self.income_account,
			"against_account_currency": self.income_account_currency,
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

	def get_double_matched_entry(self, row):
		from erpnext.accounts.utils import get_company_default

		base_gl_entry = {
			"posting_date": self.posting_date,
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"cost_center": get_company_default(self.company, "cost_center"),
			"company": self.company
		}

		# use frappe._dict to make a copy of the dict and don't modify the original
		debit_gl_entry = frappe._dict(base_gl_entry).update({
			"account": row.against_account,
			"account_currency": row.against_account_currency,
			"against": self.party,
			"debit": row.base_allocated_amount,
			"debit_in_account_currency": row.allocated_amount,
		})

		# use frappe._dict to make a copy of the dict and don't modify the original
		credit_gl_entry = frappe._dict(base_gl_entry).update({
			"party_type": self.party_type,
			"party": self.party,
			"account": row.account,
			"account_currency": row.account_currency,
			"against": row.against_account,
			"credit": row.base_allocated_amount,
			"credit_in_account_currency": row.allocated_amount,
		})

		return [debit_gl_entry, credit_gl_entry]

	def make_gl_entries(self, cancel=False, adv_adj=False):
		from erpnext.accounts.general_ledger import make_gl_entries

		gl_map = []
		for row in self.income_receipt_items:
			gl_map += self.get_double_matched_entry(row)
			
		make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, merge_entries=False)

	def update_loan_charges(self, cancel=False):
		for row in self.income_receipt_items:
			loan_charge = frappe.get_doc(row.voucher_type, row.voucher_name)

			if not cancel:
				loan_charge.paid_amount += row.allocated_amount
				loan_charge.outstanding_amount -= row.allocated_amount
			else:
				loan_charge.paid_amount -= row.allocated_amount
				loan_charge.outstanding_amount += row.allocated_amount

			loan_charge.update_references(cancel=cancel)
			loan_charge.update_status()
			loan_charge.submit()

		frappe.get_doc(self.meta.get_field("loan").options, self.loan)\
			.sync_this_with_loan_charges()

	def validate_income_receipt_items(self):

		for row in self.income_receipt_items:
			if cstr(row.repayment_date) < nowdate() and not flt(row.allocated_amount):
				frappe.throw(_("""Missing allocated amount for due Loan Charge in row: {}
					""".format(row.idx)))
