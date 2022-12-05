# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import fimax.utils
import frappe
from fimax import compound, simple
from fimax.api import create_loan_from_appl
from fimax.api import rate_to_decimal as dec
from fimax.utils import (biweekly, daily, delete_doc, half_yearly, monthly,
                         quartely, weekly, yearly)
from frappe import _ as __
from frappe import db
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, today

current_loan_schedule = None


class Loan(Document):
    @frappe.whitelist()
    def validate(self):
        loan_schedule_ids = [row.name.split()[0]
                             for row in self.loan_schedule]

        if __("New") in loan_schedule_ids:
            self.set_missing_values()

        self.update_dates()
        self.validate_company()
        self.validate_currency()
        self.validate_party_account()
        self.validate_customer_references()
        self.validate_exchange_rate()

    def before_insert(self):
        # if not self.loan_application:
        # 	frappe.throw(__("Missing Loan Application!"))
        global current_loan_schedule

        current_loan_schedule = self.loan_schedule

        for row in self.loan_schedule:
            row.name = None

        self.loan_schedule = list()

        self.validate_loan_application()

    def after_insert(self):
        self.update_status(new_status="Open")
        for row in current_loan_schedule:
            d = self.append("loan_schedule", row.as_dict())
            d.insert()

    def update_status(self, new_status=None):
        if not new_status:
            return

        options = self.meta.get_field("status").options
        options_list = options.split("\n")

        self.status = new_status

        self.validate_value("status", "in", options_list, raise_exception=True)

    def toggle_paused_status(self, paused=True):
        self.update_status("Paused" if paused else "Disbursed")

    def toggle_recovered_status(self, recovered=True):
        self.update_status("Recovered" if recovered else "Disbursed")

    def create_loan_record(self):
        # let's create the a Loan Record for future follow up
        fimax.utils.create_loan_record(self.as_dict())

    def before_submit(self):
        self.status = "Disbursed"  # duplicated with line 71?
        self.create_loan_record()

    def on_submit(self):
        self.make_gl_entries(cancel=False)
        self.commit_to_loan_charges()
        self.update_status(new_status="Disbursed")
        self.create_payment_entry_if_needed()

    def before_cancel(self):
        self.make_gl_entries(cancel=True)
        self.rollback_from_loan_charges()
        self.update_status(new_status="Cancelled")

        frappe.db.sql(f"""
			Delete from `tabGL Entry`
			where voucher_type = "Loan"
			and voucher_no = "{self.name}"
		""")

    def on_cancel(self):
        pass

    def on_trash(self):
        record = db.exists("Loan Record", self.name)

        if record:
            record = frappe.get_doc("Loan Record", self.name)
            delete_doc(record)

    @frappe.whitelist()
    def cancel_loan(self):
        self.cancel()

    @frappe.whitelist()
    def make_loan(self):
        if self.loan_application:
            loan_appl = frappe.get_doc(self.meta.get_field("loan_application").options,
                                       self.loan_application)

            self.evaluate_loan_application(loan_appl)

            return create_loan_from_appl(loan_appl)

    def create_payment_entry_if_needed(self):
        if not self.sales_invoice:
            return "We don't have a Sales Invoice to create a Payment Entry"

        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
        payment = get_payment_entry(dt="Sales Invoice", dn=self.sales_invoice)

        payment.mode_of_payment = self.get_mode_of_payment_for_pe()

        if not payment.mode_of_payment:
            known_mops = self.get_known_mops(as_set=True)
            frappe.throw(
                __("Please create a Mode of Payment with one of the following names: {0}")
                .format(frappe.utils.comma_or(known_mops))
            )

        payment.reference_no = self.name
        payment.reference_date = today()

        payment.submit()

        frappe.msgprint(
            __("Payment Entry {0} created successfully")
            .format(f"<a href=\"/app/payment-entry/{payment.name}\">{payment.name}</a>")
        )

    def get_mode_of_payment_for_pe(self):
        args = {
            "known_mops": self.get_known_mops(),
        }

        results = db.sql("""
            Select
                name
            From
                `tabMode of Payment`
            Where
                name in %(known_mops)s
            """, args, as_list=True
                         )

        return results[0][0] if results else None

    def get_known_mops(self, as_set=False):
        known_mops = [
            "Loan",
            __("Loan"),
            "Loan Payment",
            __("Loan Payment"),
        ]

        if as_set:
            return set(known_mops)

        return known_mops

    def validate_customer_references(self):
        req_references = frappe.get_value(
            "Custom Loan", self.loan_type, "customer_references")

        if self.party_type == "Customer" and \
                len(frappe.get_list("Customer Reference", {"parent": self.party})) < req_references:
            frappe.throw(
                __("This loan type requires at least %d customer references") % req_references)

    @frappe.whitelist()
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

            self.append("loan_schedule", row.update({
                "status": "Pending",
                # "repayment_date": repayment_date,
                "outstanding_amount": row.repayment_amount,
                "paid_amount": 0.000
            }))

        self.set_accounts()
        self.set_company_currency()
        self.tryto_get_exchange_rate()

        self.update_dates()

    def update_dates(self):
        for row in self.loan_schedule:
            row.repayment_date = frappe._dict({
                "Daily": daily,
                "Weekly": weekly,
                "BiWeekly": biweekly,
                "Monthly": monthly,
                "Quartely": quartely,
                "Half-Yearly": half_yearly,
                "Yearly": yearly
            }).get(self.repayment_frequency)(self.disbursement_date, row.idx)

    @frappe.whitelist()
    def set_accounts(self):
        self.set_party_account()
        income_account = frappe.get_value(
            "Company", self.company, "default_income_account")

        default_mode_of_payment = db.get_single_value(
            "Control Panel", "default_mode_of_payments")

        if not default_mode_of_payment:
            frappe.msgprint(
                __("Please set a default mode of payment in the Control Panel"))

        if not self.income_account:
            self.income_account = income_account

        if not self.mode_of_payment and default_mode_of_payment:
            self.mode_of_payment = default_mode_of_payment

        if not self.disbursement_account:
            self.disbursement_account = frappe.get_value(
                "Company", self.company, "default_bank_account")

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

        if self.party_account:
            return

        if self.party_type in ("Customer", "Supplier"):
            self.party_account = get_party_account(
                self.party_type, self.party, self.company)
        else:
            default_receivable = frappe.get_value(
                "Company", self.company, "default_receivable_account")

            first_receivable = frappe.get_value("Account", {
                "account_type": "Receivable",
                "company": self.company,
                "account_currency": self.currency
            })

            self.party_account = default_receivable or first_receivable

    def set_company_currency(self):
        default_currency = frappe.get_value(
            "Company", self.company, "default_currency")
        self.company_currency = default_currency

    def tryto_get_exchange_rate(self):
        if not self.exchange_rate == 1.000:
            return

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

    @frappe.whitelist()
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
            frappe.throw(
                __("Selected party account does not belong to Loan's Company!"))

        if not account_type == "Receivable":
            frappe.throw(__("Selected party account is not Receivable!"))

        if not currency == self.currency:
            frappe.throw(
                __("Customer's currency and Loan's currency must be the same, you may want to create a new customer with the desired currency if necessary!"))

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
            frappe.throw(
                __("The selected Loan Application is already cancelled!"))

        if db.exists("Loan", {
            "loan_application": loan_appl.name,
            "docstatus": ["!=", "2"]
        }):
            frappe.throw(
                __("Loan Application: {0} already attached to another Loan")
                .format(self.loan_application)
            )

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

        for idx, loan_repayment in enumerate(self.loan_schedule):
            self.publish_realtime(idx + 1, records)

            args_list = [("Capital", loan_repayment.capital_amount)]

            if loan_repayment.interest_amount:
                args_list += [("Interest", loan_repayment.interest_amount)]

            if not db.get_single_value("Control Panel", "detail_repayment_amount"):
                args_list = [
                    ("Repayment Amount", loan_repayment.repayment_amount)]

            for loan_charges_type, amount in args_list:
                loan_charges = loan_repayment.get_new_loan_charge(
                    loan_charges_type, amount)
                loan_charges.currency = self.currency

                # tell the loan_charges not to create the General Ledger Entries
                loan_charges.flags.dont_update_gl_entries = True

                # update status to make sure it has the right one
                loan_charges.update_status()

                # finally create it and submit it
                loan_charges.submit()

    def rollback_from_loan_charges(self):
        records = len(self.loan_schedule) or 1

        for idx, loan_repayment in enumerate(self.loan_schedule):
            self.publish_realtime(idx + 1, records)

            [self.cancel_and_delete_loan_charge(loan_repayment, loan_charges_type)
                for loan_charges_type in ('Capital', 'Interest', 'Repayment Amount')]

    def cancel_and_delete_loan_charge(self, child, loan_charges_type):

        loan_charge = child.get_loan_charge(loan_charges_type)

        if not loan_charge or not loan_charge.name:
            return

        doc = frappe.get_doc("Loan Charges", loan_charge.name)

        if not doc.is_elegible_for_deletion():
            frappe.throw(__("Could not cancel this Loan because the loan charge <i>{1}</i>:<b>{0}</b> is not pending anymore!"
                            .format(doc.name, doc.loan_charges_type)))

        delete_doc(doc)

        db.commit()

    def get_double_matched_entry(self, amount, against, voucher_type=None, voucher_no=None):
        from erpnext.accounts.utils import get_company_default

        if not voucher_type and not voucher_no:
            voucher_type = self.doctype
            voucher_no = self.name

        base_gl_entry = {
            "posting_date": self.posting_date,
            "voucher_type": voucher_type,
            "voucher_no": voucher_no,
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

        gl_map = list()
        if lent_amount:
            gl_map += self.get_double_matched_entry(
                lent_amount, self.disbursement_account)

        # check to see for the posibility to use another account for legal_expenses income
        if flt(self.legal_expenses_amount) > 0:
            gl_map += self.get_double_matched_entry(
                self.legal_expenses_amount, self.income_account)

        if flt(self.total_interest_amount) > 0:
            gl_map += self.get_double_matched_entry(
                self.total_interest_amount, self.income_account)

        make_gl_entries(gl_map, cancel=cancel,
                        adv_adj=adv_adj, merge_entries=False)

    @frappe.whitelist()
    def sync_this_with_loan_charges(self):
        records = len(self.loan_schedule) or 1

        for idx, row in enumerate(self.loan_schedule):
            self.publish_realtime(idx + 1, records)

            paid_amount, last_status = db.get_value("Loan Charges", filters={
                "docstatus": 1,
                "status": ["!=", "Closed"],
                "reference_type": row.doctype,
                "reference_name": row.name,
            }, fieldname=[
                "SUM(paid_amount)",
                "status"], order_by="name ASC")

            row.paid_amount = flt(paid_amount)
            row.outstanding_amount = flt(
                row.repayment_amount - row.paid_amount)
            row.status = last_status or row.status
            row.submit()

        self.update_index_for_loan_schedule()

    def update_index_for_loan_schedule(self):
        index = 1
        for each in sorted(self.loan_schedule, key=lambda d: d.repayment_date):
            each.idx = index
            index += 1
            each.db_update()

    def publish_realtime(self, current, total):
        frappe.publish_realtime("real_progress", {
            "progress": flt(current) / flt(total) * 100,
        }, user=frappe.session.user)
