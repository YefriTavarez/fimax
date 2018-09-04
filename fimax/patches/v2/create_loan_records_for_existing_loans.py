import frappe
from fimax.utils import create_loan_record

def execute():

	doctype = "Loan"
	for docname, in frappe.get_list(doctype, {
		"docstatus": ["<", "2"]
	}, ["name"], as_list=True):
		doc = frappe.get_doc(doctype, docname)

		create_loan_record(doc)