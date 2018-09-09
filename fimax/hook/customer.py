import frappe
from frappe import _
import json

def validate(doc, event):
	
	doc = doc.as_dict()
	references = len(doc.customer_reference)

	result = frappe.db.sql("""
		SELECT
			l.name as loan, l.loan_type, MAX(cl.customer_references) as customer_references, l.party
		FROM
			`tabLoan` l
		JOIN
			`tabCustom Loan` cl
		ON
			l.loan_type = cl.loan_name
		WHERE 
			l.party_type = "Customer" 
		AND 
			l.status not in ('Closed', 'Cancelled')
		AND
			l.party = %s
		AND 
			cl.customer_references > %s

		GROUP BY l.name	""",(doc.customer_name, references), as_dict=True, debug=True)
	
	if result:
		frappe.throw(_("""This customer requires at least {customer_references} 
			references according to loan {loan}""").format(**result[0]))

