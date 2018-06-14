import frappe

def all():
	pass

def daily():
	update_status_to_loan_charges()

def hourly():
	pass

def weekly():
	pass

def monthly():
	pass

def update_status_to_loan_charges():
	for doc in get_valid_loan_charges():
		if not frappe.db.exists(doc.doctype, 
			doc.name): return

		# it exists, so then let's get it
		doc = frappe.get_doc(doc.doctype, doc.name)

		doc.update_status()

		# submit to update the database
		doc.submit()

	# after finishing with all the items then commit the changes
	frappe.db.commit()

def get_valid_loan_charges():
	return frappe.db.sql("""SELECT 
			loan_charges.name AS name, 
			'Loan Charges' AS doctype
		FROM
			`tabLoan Charges` AS loan_charges
		JOIN
			`tabLoan Charges Type` AS loan_charges_type 
			ON loan_charges.loan_charges_type = loan_charges_type.name
		WHERE loan_charges_type.generates_fine > 0
			AND TIMESTAMPDIFF(MONTH, loan_charges.modified, CURRENT_TIMESTAMP) > 0
			AND loan_charges_type.repayment_date < CURDATE()
				AND loan_charges.status NOT IN ('Paid' , 'Closed')""", as_dict=True)