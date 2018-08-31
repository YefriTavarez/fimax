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
from fimax.utils import delete_doc

from frappe.utils import flt, cint, cstr
from frappe import _ as __

class Loan(Document):
	def validate(self):
		loan_schedule_ids = [row.name.split()[0] 
			for row in self.loan_schedule]
			
		if __("New") in loan_schedule_ids:
			self.set_missing_values()

		self.update_repayment_schedule_dates()
		self.validate_company()
		self.validate_currency()
		self.validate_party_account()
		self.validate_exchange_rate()

	def before_insert(self):
		if not self.loan_application:
			frappe.throw(__("Missing Loan Application!"))

		self.validate_loan_application()

	def after_insert(self):
		# Let's create the a Loan Record for future follow up.
		record = frappe.new_doc("Loan Record")
		record.loan = self.name 
		record.party_type = self.party_type 
		record.party = self.party 
		record.insert(ignore_permissions=True)

	def update_status(self, new_status):
		options = self.meta.get_field("status").options
		options_list = options.split("\n")

		self.status = new_status

		self.validate_value("status", "in", options_list, raise_exception=True)

	def toggle_paused_status(self, paused=True):
		self.update_status("Paused" if paused else "Disbursed")

	def toggle_recovered_status(self, recovered=True):
		self.update_status("Recovered" if recovered else "Disbursed")

	def before_submit(self):
		self.status = "Disbursed"

	def on_submit(self):
		self.make_gl_entries(cancel=False)
		self.commit_to_loan_charges()
		self.update_status(new_status="Disbursed")

	def before_cancel(self):
		self.make_gl_entries(cancel=True)
		self.rollback_from_loan_charges()
		self.update_status(new_status="Cancelled")

	def on_cancel(self):
		pass

	def on_trash(self):
		record = frappe.db.exists("Loan Record", self.name)

		if record:
			record = frappe.get_doc("Loan Record", self.name)
			delete_doc(record) 

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

			self.append("loan_schedule", row.update({
				"status": "Pending",
				"repayment_date": self.get_correct_date(repayment_date),
				"outstanding_amount": row.repayment_amount,
				"paid_amount": 0.000
			}))

		self.set_accounts()
		self.set_company_currency()
		self.tryto_get_exchange_rate()

	def set_accounts(self):
		self.set_party_account()
		income_account = frappe.get_value("Company", self.company, "default_income_account")

		default_mode_of_payment = frappe.db.get_single_value("Control Panel", "default_mode_of_payments")

		if not self.income_account:
			self.income_account = income_account

		if not self.mode_of_payment:
			self.mode_of_payment = default_mode_of_payment
			
		if not self.mode_of_payment:
			self.mode_of_payment = default_mode_of_payment
			
		self.disbursement_account = frappe.get_value("Company", self.company, "default_bank_account")
		
	def get_correct_date(self, repayment_date):
		last_day_of_the_month = frappe.utils.get_last_day(repayment_date)
		first_day_of_the_month = frappe.utils.get_first_day(repayment_date)

		if cint(self.repayment_day_of_the_month) > last_day_of_the_month.day:
			return last_day_of_the_month.replace(last_day_of_the_month.year, 
				last_day_of_the_month.month, last_day_of_the_month.day)
		else:
			return frappe.utils.add_days(first_day_of_the_month, 
				cint(self.repayment_day_of_the_month) - 1)

	def set_party_account(self):
		from erpnext.accounts.party import get_party_account

		if self.party_account: return

		if self.party_type in ("Customer", "Supplier"):
			self.party_account = get_party_account(self.party_type, self.party, self.company)
		else:
			default_receivable = frappe.get_value("Company", self.company, "default_receivable_account")

			first_receivable = frappe.get_value("Account", {
				"account_type": "Receivable",
				"company": self.company,
				"account_currency": self.currency
			})

			self.party_account =  default_receivable or first_receivable

	def set_company_currency(self):
		default_currency = frappe.get_value("Company", self.company, "default_currency")
		self.company_currency = default_currency

	def tryto_get_exchange_rate(self):
		if not self.exchange_rate == 1.000:	return

		# the idea is to get the filters in the two possible combinations
		# ex.
		# 1st => { u'from_currency': u'USD', u'to_currency': u'INR' }
		# 2nd => { u'from_currency': u'INR', u'to_currency': u'USD' }

		field_list = ["from_currency", "to_currency"]
		currency_list = [self.currency, self.company_currency]

		purchase_bank_rate = frappe.get_value("Currency Exchange", 
			dict(zip(field_list, currency_list)), "exchange_rate", order_by="date DESC")

		# reverse the second list to get the second combination
		currency_list.reverse()

		sales_bank_rate = frappe.get_value("Currency Exchange", 
			dict(zip(field_list, currency_list)), "exchange_rate", order_by="date DESC")

		self.exchange_rate = purchase_bank_rate or sales_bank_rate or 1.000

	def update_repayment_schedule_dates(self):
		for row in self.loan_schedule:
			row.repayment_date = self.get_correct_date(row.repayment_date) 

	def validate_currency(self):
		if not self.currency:
			frappe.throw(__("Currency for Loan is mandatory!"))
		
	def validate_company(self):
		if not self.company:
			frappe.throw(__("Company for Loan is mandatory!"))

	def validate_party_account(self):
		if not self.party_account:
			frappe.throw(__("Party Account for Loan is mandatory!"))
			
		company, account_type, currency = frappe.get_value("Account",
			self.party_account, ["company", "account_type", "account_currency"])

		if not company == self.company:
			frappe.throw(__("Selected party account does not belong to Loan's Company!"))

		if not account_type == "Receivable":
			frappe.throw(__("Selected party account is not Receivable!"))

		if not currency == self.currency:
			frappe.throw(__("Customer's currency and Loan's currency must be the same, you may want to create a new customer with the desired currency if necessary!"))

	def validate_exchange_rate(self):
		if not self.exchange_rate:
			frappe.throw(__("Unexpected exchange rate"))

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

	def get_base_amount_for(self, fieldname):
		if not self.meta.get_field(fieldname).fieldtype in ('Currency', 'Float'):
			frappe.throw(__("Field Type for {fieldname} is not aplicable to be returned\
				as Base Amount".format(fieldname=fieldname)))

		return self.get(fieldname) * self.exchange_rate
	def get_lent_amount(self):
		return flt(self.loan_amount) - flt(self.legal_expenses_amount)

	def commit_to_loan_charges(self):
		from fimax.install import add_default_loan_charges_type
		
		records = len(self.loan_schedule) or 1

		# run this to make sure default loan charges type are set
		add_default_loan_charges_type()

		for idx, row in enumerate(self.loan_schedule):
			self.publish_realtime(idx + 1, records)
			
			args_list = [("Capital", row.capital_amount)]
			args_list += [("Interest", row.interest_amount)]

			if not frappe.db.get_single_value("Control Panel", "detail_repayment_amount"):
				args_list = [("Repayment Amount", row.repayment_amount)]

			for args in args_list:
				lc = row.get_new_loan_charge(*args)
				lc.currency = self.currency

				lc.update_status()
				lc.submit()

	def rollback_from_loan_charges(self):
		records = len(self.loan_schedule) or 1
			
		for idx, row in enumerate(self.loan_schedule):
			self.publish_realtime(idx + 1, records)

			[self.cancel_and_delete_loan_charge(row, loan_charges_type) 
				for loan_charges_type in ('Capital', 'Interest', 'Repayment Amount')]

	def cancel_and_delete_loan_charge(self, child, loan_charges_type):
		
		loan_charge = child.get_loan_charge(loan_charges_type)

		if not loan_charge or not loan_charge.name: return
		
		doc = frappe.get_doc("Loan Charges", loan_charge.name)

		if not doc.is_elegible_for_deletion():
			frappe.throw(__("Could not cancel this Loan because the loan charge <i>{1}</i>:<b>{0}</b> is not pending anymore!"
				.format(doc.name, doc.loan_charges_type)))

		delete_doc(doc)

		frappe.db.commit()

	def get_double_matched_entry(self, amount, against):
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
			"party_type": self.party_type,
			"party": self.party,
			"account": self.party_account,
			"account_currency": frappe.get_value("Account", self.party_account, "account_currency"),
			"against": against,
			"debit": flt(amount) * flt(self.exchange_rate),
			"debit_in_account_currency": flt(amount),
		})

		# use frappe._dict to make a copy of the dict and don't modify the original
		credit_gl_entry = frappe._dict(base_gl_entry).update({
			"account": against,
			"account_currency": frappe.get_value("Account", against, "account_currency"),
			"against": self.party,
			"credit":  flt(amount) * flt(self.exchange_rate),
			"credit_in_account_currency": flt(amount),
		})
		
		return [debit_gl_entry, credit_gl_entry]

	def make_gl_entries(self, cancel=False, adv_adj=False):
		from erpnext.accounts.general_ledger import make_gl_entries

		# amount that was disbursed from the bank account
		lent_amount = self.get_lent_amount()

		gl_map = self.get_double_matched_entry(lent_amount, self.disbursement_account)
		# check to see for the posibility to use another account for legal_expenses income
		gl_map += self.get_double_matched_entry(self.legal_expenses_amount, self.income_account)
		gl_map += self.get_double_matched_entry(self.total_interest_amount, self.income_account)

		make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, merge_entries=False)

	def sync_this_with_loan_charges(self):
		records = len(self.loan_schedule) or 1

		for idx, row in enumerate(self.loan_schedule):
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