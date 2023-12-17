# -*- coding: utf-8 -*-
# Copyright (c) 2017, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe import _ as __
from fimax.api import create_loan_from_appl
from fimax.api import rate_to_decimal as dec

from fimax import simple, compound
from frappe.utils import flt, cstr, cint, nowdate
from fimax.utils import validate_comment_on_cancel


class LoanApplication(Document):
    @frappe.whitelist()
    def validate(self):
        self.set_missing_values()
        self.set_approved_amounts()
        self.validate_approved_amounts()
        self.validate_customer_references()
        self.calculate_legal_expenses_amount()
        self.set_repayment_amount()

    def on_update_after_submit(self):
        self.validate_approved_amounts()

    def before_insert(self):
        pass

    def after_insert(self):
        pass

    def before_submit(self):
        pass

    def on_submit(self):
        pass

    def before_cancel(self):
        pass

    def on_cancel(self):
        user = frappe.session.user
        validate_comment_on_cancel(user=user, doctype=self.doctype, docname=self.name)

    def on_trash(self):
        pass

    def calculate_legal_expenses_amount(self):
        self.legal_expenses_amount = flt(self.approved_gross_amount) \
            * dec(self.legal_expenses_rate)

    def make_loan(self):
        return create_loan_from_appl(self)

    def set_missing_values(self):
        if not self.posting_date:
            self.posting_date = frappe.utils.nowdate()

    def set_approved_amounts(self):
        if frappe.session.user == self.owner:
            if self.docstatus == 1 and not self.approved_gross_amount == self.requested_gross_amount:
                frappe.msgprint(
                    __("You won't be able to change the approved amount as you are the one requesting!")
                )

            self.approved_gross_amount = self.requested_gross_amount

    def validate_approved_amounts(self):
        loan_type_field = self.meta.get_field("loan_type")

        maximum_loan_amount = frappe.get_value(loan_type_field.options,
                                               self.loan_type, "maximum_loan_amount")

        if self.requested_net_amount > flt(maximum_loan_amount):
            frappe.throw(
                __("Requested Net Amount can not be greater than the Maximum Loan Amount in this Loan Type"))

        if self.approved_gross_amount > self.requested_gross_amount:
            frappe.throw(
                __("Approved Amount can not be greater than Requested Amount"))

    def validate_required_fields_for_repayment_amount(self):
        if not self.approved_net_amount:
            frappe.throw(__("Missing Approved Net Amount"))

        # if not self.interest_rate:
        # 	frappe.throw(__("Missing Interest Rate"))

        if not self.repayment_periods:
            frappe.throw(__("Missing Repayment Periods"))

    def validate_customer_references(self):
        req_references = frappe.get_value(
            "Custom Loan", self.loan_type, "customer_references")

        if self.party_type == "Customer" and \
                len(frappe.get_list("Customer Reference", {"parent": self.party})) < req_references:
            frappe.throw(
                __("This loan type requires at least %d customer references") % req_references)

    def set_repayment_amount(self):
        # simple or compound variable
        soc = simple

        self.validate_required_fields_for_repayment_amount()

        if self.interest_type == "Compound":
            soc = compound

        self.repayment_amount = soc.get_repayment_amount(self.approved_net_amount,
                                                         dec(self.interest_rate), self.repayment_periods)


@frappe.whitelist()
def create_from_sales_invoice(sales_invoice):
    invoice_details = get_sales_invoice(sales_invoice)

    doctype = "Loan Application"
    appl = frappe.new_doc(doctype)

    loan_type = get_loan_type()

    appl.update({
        "party_type": "Customer",
        "party": invoice_details.customer,
        "party_name": invoice_details.customer_name,
        "sales_invoice": invoice_details.name,
        "posting_date": invoice_details.posting_date,
        "loan_type": loan_type,
        "interest_type": "Simple",
        "interest_rate": 0,
        "legal_expenses_rate": 5,
        "requested_gross_amount": invoice_details.outstanding_amount,
        "approved_gross_amount": invoice_details.outstanding_amount, 
        "requested_net_amount": invoice_details.outstanding_amount,
        "approved_net_amount": invoice_details.outstanding_amount,
        "repayment_periods": 12,
        "repayment_day_of_the_month": get_repayment_day_of_the_month(),
        "user_remarks": get_user_remarks(),
    })
    appl.validate()
   
    # small fix for the moment
    appl.requested_net_amount = \
        flt(appl.legal_expenses_amount) \
        + flt(appl.requested_gross_amount)

    appl.approved_net_amount = \
        flt(appl.legal_expenses_amount) \
        + flt(appl.approved_gross_amount)

    appl.set_repayment_amount()

    return appl


def get_sales_invoice(name):
    doctype = "Sales Invoice"
    return frappe.get_doc(doctype, name)


def get_loan_type():
    doctype = "Custom Loan"

    doc = frappe.get_last_doc(doctype)

    if not doc:
        frappe.throw(__("No Loan Types found"))

    return doc.name


def get_repayment_day_of_the_month():
    today = nowdate()

    day_of_month, _, __ = today.split("-")
    return cstr(
        cint(day_of_month) % 30
    )


def get_user_remarks():
    return "Created from Sales Invoice pay remaining amount on a monthly basis"
