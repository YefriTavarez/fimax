import frappe

from enum import Enum

class DocStatus(Enum):
	DRAFT = 0
	SUBMITTED = 1
	CANCELLED = 2

def delete_doc(doc, ignore_permissions=False):
	if DocStatus(doc.docstatus) is DocStatus.SUBMITTED:
		doc.cancel(ignore_permissions=ignore_permissions)
	doc.delete(ignore_permissions=ignore_permissions)
