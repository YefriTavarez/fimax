import frappe

from frappe.utils import cint, flt, cstr
from frappe.utils import nowdate, add_days, add_months

def all():
	pass

def daily():
	update_status_to_loan_charges()
	create_loan_charges_fines()
	
	# after finishing with all items then commit the changes
	frappe.db.commit()

def hourly():
	pass

def weekly():
	pass

def monthly():
	pass

def update_status_to_loan_charges():
	"""Update status for each Loan Charge based on the current date and the paid amount"""
	for doc in get_valid_loan_charges():
		if not frappe.db.exists(doc.doctype, 
			doc.name): return

		# it exists, so then let's get it
		doc = frappe.get_doc(doc.doctype, doc.name)

		doc.update_status()

		# submit to update the database
		doc.submit()

def create_loan_charges_fines():
	for company, in frappe.get_list("Company", as_list=True):
		create_loan_charges_fines_for_(company)
			
def create_loan_charges_fines_for_(company):
	if not frappe.db.exists("Company Defaults", {
		"company": company
	}): return

	company_defaults = frappe.get_doc("Company Defaults", {
		"company": company
	}).as_dict()

	today = nowdate()
	
	due_date = today

	if company_defaults.grace_days:
		due_date = add_days(today, - cint(company_defaults.grace_days))

	late_payment_fee_rate = company_defaults.late_payment_fee_rate / 100.000
	late_payment_fee_on_total_amount = company_defaults.late_payment_fee_on_total_amount

	doctype = "Loan Charges"

	for name, in frappe.get_list(doctype, {
		"status": "Overdue",
		"repayment_date": [">=", due_date]
	}, as_list=True):

		reference_type, reference_name = frappe.get_value(doctype, name, 
			["reference_type", "reference_name"])

		total_amount, outstanding_amount = frappe.get_value(doctype, name, 
			["total_amount", "outstanding_amount"])
		
		doc = frappe.get_doc(reference_type, reference_name)

		time_to_run = None
		
		if doc.last_run:
			time_to_run = add_months(doc.last_run, 1)

		if time_to_run and not cstr(time_to_run) <= nowdate():
			return

		amount = late_payment_fee_rate * total_amount if late_payment_fee_on_total_amount \
			else outstanding_amount

		loan_charges = doc.get_new_loan_charge("Late Payment Fee", amount)
		# loan_charges.repayment_date = add_months(loan_charges.posting_date, 1)

		if amount:
			doc.last_run = nowdate()
			doc.db_update()

			loan_charges.submit()

def get_valid_loan_charges():
	return frappe.db.sql("""SELECT 
			loan_charges.name AS name, 
			'Loan Charges' AS doctype
		FROM
			`tabLoan Charges` AS loan_charges
		INNER JOIN
			`tabLoan Charges Type` AS loan_charges_type 
			ON loan_charges.loan_charges_type = loan_charges_type.name
		WHERE loan_charges_type.generates_fine > 0
			AND TIMESTAMPDIFF(MONTH, loan_charges.modified, CURRENT_TIMESTAMP) > 0
			AND loan_charges.repayment_date < CURDATE()
				AND loan_charges.status NOT IN ('Paid' , 'Closed')""", as_dict=True)
