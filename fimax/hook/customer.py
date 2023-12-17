import frappe
from frappe import _

def validate(doc, event):
	
	references = len(doc.customer_reference)

	result = frappe.db.sql("""SELECT
			`tabLoan`.name,
			`tabLoan`.loan_type, 
			`tabLoan`.party,
			MAX(`tabCustom Loan`.customer_references) AS customer_references
		FROM `tabLoan`
		INNER JOIN `tabCustom Loan`
			ON `tabLoan`.loan_type = `tabCustom Loan`.loan_name
		WHERE `tabLoan`.party_type = "Customer" 
			AND `tabLoan`.status NOT IN ('Closed', 'Cancelled')
			AND `tabLoan`.party = %s
			AND `tabCustom Loan`.customer_references > %s
		GROUP BY `tabLoan`.name""", (doc.customer_name, references),
	as_dict=True)
	
	if not result: return
	
	frappe.throw(_("""This customer requires at least {customer_references} 
		references according to loan {name}""").format(**result[0]))
