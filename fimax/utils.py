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
