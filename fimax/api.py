import frappe, json

from frappe.utils import flt, cint

def rate_to_decimal(rate):
	"""Converts from percentage format to decimal"""
	return flt(rate) / flt(100.000)

@frappe.whitelist()
def create_loan_from_appl(doc):
	from frappe.model.mapper import get_mapped_doc

	if isinstance(doc, basestring):
		doc = frappe._dict(json.loads(doc))

	def post_process(source_doc, target_doc):
		target_doc.set_missing_values()

	target_doc = frappe.new_doc("Loan")

	return get_mapped_doc(doc.doctype, doc.name, {
		"Loan Application": {
			"doctype": "Loan",
			"field_map": {
				"name": "loan_application",
				"approved_net_amount": "loan_amount"
			}
		}
	}, target_doc, post_process)

@frappe.whitelist()
def get_loan(doctype, docname):
	doc = frappe.get_doc(doctype, docname)

	income_account_currency = frappe.get_value("Account", 
		doc.income_account, "account_currency")

	doc.set_onload("income_account_currency", income_account_currency)

	return doc.as_dict()

@frappe.whitelist()
def create_insurance_card_from_loan(doc):
	from frappe.model.mapper import get_mapped_doc

	if isinstance(doc, basestring):
		doc = frappe._dict(json.loads(doc))

	def post_process(source_doc, target_doc):
		target_doc.set_default_values()

	target_doc = frappe.new_doc("Insurance Card")

	return get_mapped_doc(doc.doctype, doc.name, {
		"Loan": {
			"doctype": "Insurance Card"
		}
	}, target_doc, post_process)
