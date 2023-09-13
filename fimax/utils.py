import frappe
from frappe.utils import add_to_date, cint, flt, nowdate
from erpnext.setup.utils import get_exchange_rate
from enum import Enum
from frappe import _


class DocStatus(Enum):
    DRAFT = 0
    SUBMITTED = 1
    CANCELLED = 2


def delete_doc(doc):
    if DocStatus(doc.docstatus) is DocStatus.SUBMITTED:
        doc.cancel()

    try:
        doc.delete()
    except:
        pass


def create_loan_record(doc):
    """Creates a Loan Record given the Loan doc"""
    record = frappe.new_doc("Loan Record")

    record.update({
        "loan": doc.name,
        "status": doc.status,
        "party_type": doc.party_type,
        "party": doc.party
    })

    return record.insert(ignore_permissions=True)


def daily(date, idx):
    return add_to_date(date, days=cint(idx))


def weekly(date, idx):
    return add_to_date(date, days=cint(idx) * 7)


def biweekly(date, idx):
    return add_to_date(date, days=cint(idx) * 14)


def monthly(date, idx):
    return add_to_date(date, months=cint(idx))


def quartely(date, idx):
    return add_to_date(date, months=cint(idx) * 3)


def half_yearly(date, idx):
    return add_to_date(date, months=cint(idx) * 6)


def yearly(date, idx):
    return add_to_date(date, years=cint(idx))


def apply_changes_from_quick_income_receipt(doc, insurance_amount=.000, gps_amount=.000, capital_amount=.000,
                                            interest_amount=.000, repayment_amount=.000, recovery_amount=.000, fine_amount=.000, total_amount=.000, advance_to_capital=False):
    # skip if the user didn't send any amount
    if not total_amount:
        return

    # clear the table
    doc.set("income_receipt_items", [])

    charges_types = get_charges_types(insurance_amount, gps_amount, capital_amount,
                                      interest_amount, repayment_amount, recovery_amount, fine_amount, advance_to_capital)

    loan_doc = frappe.get_doc(doc.meta.get_field("loan").options, doc.loan)

    doc.income_account, doc.income_account_currency = doc.get_income_account_and_currency(
        loan_doc)

    doc.exchange_rate = get_exchange_rate(
        loan_doc.currency, doc.income_account_currency)
    doc.currency = frappe.get_value("Company", doc.company, "default_currency")

    non_paid_charges = doc.list_loan_charges(ignore_repayment_date=True)
    interest_charges_by_idx = get_non_paid_interests_by_idx(non_paid_charges)

    # this var will be used to write off the interest if advance_to_capital = True
    total_interest_write_off = 0.000
    for charge in non_paid_charges:
        loan_charge = doc.get_income_receipt_item(loan_doc, charge)
        loan_charge.allocated_amount = 0.000

        # skip if there is not money for this loan charges type
        if not loan_charge.loan_charges_type in charges_types:
            continue

        if charge.loan_charges_type == "Insurance" and insurance_amount:
            insurance_amount = get_new_amount(
                charge, loan_charge, insurance_amount)

        if charge.loan_charges_type == "Late Payment Fee" and fine_amount:
            fine_amount = get_new_amount(charge, loan_charge, fine_amount)

        if charge.loan_charges_type == "GPS" and gps_amount:
            gps_amount = get_new_amount(charge, loan_charge, gps_amount)

        if charge.loan_charges_type == "Capital" and capital_amount:
            capital_amount = get_new_amount(
                charge, loan_charge, capital_amount)

        if charge.loan_charges_type == "Interest" and interest_amount:
            interest_amount = get_new_amount(
                charge, loan_charge, interest_amount)

        if charge.loan_charges_type == "Repayment Amount" and repayment_amount:
            repayment_amount = get_new_amount(
                charge, loan_charge, repayment_amount)

        if charge.loan_charges_type == "Recovery Expenses" and recovery_amount:
            recovery_amount = get_new_amount(
                charge, loan_charge, recovery_amount)

        loan_charge.base_allocated_amount = flt(
            loan_charge.allocated_amount) * flt(doc.exchange_rate)

        # skip for duplicates
        if not loan_charge.get("voucher_name") in [d.get("voucher_name")
                                                   for d in doc.income_receipt_items] and loan_charge.allocated_amount:
            doc.append("income_receipt_items", loan_charge)

        if (
            advance_to_capital
            and charge.loan_charges_type == "Capital"
            # if you want to be more strict you can do the following conditional
            # instead
            # and loan_charge.allocated_amount == loan_charge.total_amount
            and loan_charge.allocated_amount == loan_charge.outstanding_amount
        ):
            try:
                charge = interest_charges_by_idx[charge.repayment_period]
            except KeyError:
                pass
                # we might encounter with a capital charge without interest
            else:
                # if advance to capital, we want to deduct the interest from the capital
                loan_charge = doc.get_income_receipt_item(loan_doc, charge)
                loan_charge.allocated_amount = loan_charge.outstanding_amount
                loan_charge.discount = loan_charge.outstanding_amount

                total_interest_write_off += loan_charge.outstanding_amount

                doc.append("income_receipt_items", loan_charge)

    total_unallocated = get_total_unallocated(insurance_amount, gps_amount, capital_amount,
                                              interest_amount, repayment_amount, recovery_amount, fine_amount)

    if total_unallocated > 0.000:
        df = {"fieldtype": "Currency"}
        total_unallocated_formatted = \
            frappe.format_value(total_unallocated, df=df)
        frappe.msgprint(
            _("Warning: There is an unallocated balance of ${0}".format(
                total_unallocated_formatted))
        )

    if advance_to_capital:
        doc.write_off_amount = total_interest_write_off

    doc.calculate_totals()


def get_charges_types(insurance_amount=.000, gps_amount=.000, capital_amount=.000,
                      interest_amount=.000, repayment_amount=.000, recovery_amount=.000, fine_amount=.000, advance_to_capital=False):
    """Will return a list of the Loan Charges Types based on the parameters the user sent
            Posible values are: Capital, Interest, Repayment Amount,
                    Insurance, Late Payment Fee, GPS
    """
    charges_types = []

    if insurance_amount:
        charges_types.append("Insurance")

    if gps_amount:
        charges_types.append("GPS")

    if capital_amount:
        charges_types.append("Capital")

    if interest_amount or advance_to_capital:
        charges_types.append("Interest")

    if repayment_amount:
        charges_types.append("Repayment Amount")

    if recovery_amount:
        charges_types.append("Recovery Expenses")

    if fine_amount:
        charges_types.append("Late Payment Fee")

    return charges_types


def get_new_amount(charge, loan_charge, allocated_amount):
    if allocated_amount < charge.outstanding_amount:
        loan_charge.allocated_amount = allocated_amount
        allocated_amount = .000
    else:
        loan_charge.allocated_amount = charge.outstanding_amount
        allocated_amount -= charge.outstanding_amount

    return allocated_amount


def get_total_unallocated(insurance_amount=.000, gps_amount=.000, capital_amount=.000,
                          interest_amount=.000, repayment_amount=.000, recovery_amount=.000, fine_amount=.000):
    return flt(insurance_amount) + flt(gps_amount) + flt(capital_amount) + flt(interest_amount)\
        + flt(repayment_amount) + flt(recovery_amount) + flt(fine_amount)


def get_non_paid_interests_by_idx(non_paid_charges):
    interest_charges_by_idx = dict()

    for charge in non_paid_charges:
        if charge.loan_charges_type == "Interest":
            interest_charges_by_idx[charge.repayment_period] = charge

    return interest_charges_by_idx

def validate_comment_on_cancel(user, doctype, docname):
    filters={"comment_email":user, "reference_doctype":doctype, "reference_name":docname}
    if not frappe.db.exists("Comment", filters):
        frappe.throw("Favor agregar un comentario con la razon de la cancelación al pie de este documento.")