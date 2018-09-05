import frappe
from frappe.utils import add_to_date, cint, nowdate

from enum import Enum

class DocStatus(Enum):
	DRAFT = 0
	SUBMITTED = 1
	CANCELLED = 2

def delete_doc(doc):
	if DocStatus(doc.docstatus) is DocStatus.SUBMITTED:
		doc.cancel()
	doc.delete()

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
