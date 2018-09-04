import frappe

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
