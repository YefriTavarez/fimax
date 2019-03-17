import frappe

from frappe.utils import cint, flt, cstr
from frappe.utils import nowdate, add_days, add_months

from frappe import get_doc, db, _

def all():
	pass

def daily():
	update_status_to_loan_charges()
	create_loan_charges_fines()

def hourly():
	pass

def weekly():
	pass

def monthly():
	pass

def update_status_to_loan_charges():
	"""Update status for each Loan Charge based on the current date and the paid amount"""
	for doc in get_valid_loan_charges():
		if not db.exists(doc.doctype,
			doc.name): return

		# it exists, so then let's get it
		doc = get_doc(doc.doctype, doc.name)

		doc.run_method("update_references", cancel=False)

		doc.run_method("update_status")

		# submit to update the database
		doc.submit()

def create_loan_charges_fines():
	for company, in frappe.get_list("Company", as_list=True):
		create_loan_charges_fines_for_(company)

def create_loan_charges_fines_for_(company):
	if not db.exists("Company Defaults", {
		"company": company
	}): return

	company_defaults = get_doc("Company Defaults", {
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
		"docstatus": "1",
		"repayment_date": ["<=", due_date]
	}, as_list=True):

		reference_type, reference_name = frappe.get_value(doctype, name,
			["reference_type", "reference_name"])

		total_amount, outstanding_amount = frappe.get_value(doctype, name,
			["total_amount", "outstanding_amount"])

		loan_repayment = get_doc(reference_type, reference_name)

		time_to_run = None

		if loan_repayment.get("last_run"):
			time_to_run = add_months(loan_repayment.last_run, 1)

		if time_to_run and not cstr(time_to_run) <= nowdate():
			continue

		amount = late_payment_fee_rate * total_amount if late_payment_fee_on_total_amount \
			else outstanding_amount

		if hasattr(loan_repayment, "get_new_loan_charge"):
			loan_charges = loan_repayment \
				.get_new_loan_charge("Late Payment Fee",
									 amount)

		if not amount: continue

		loan_repayment.last_run = nowdate()

		loan_repayment.db_update()

		if loan_repayment.parenttype == "Loan":
			update_loan_record(
				get_doc(loan_repayment.parenttype,
					loan_repayment.parent))

		loan_charges.submit()

def get_valid_loan_charges():
	return db.sql("""SELECT
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
			AND loan_charges.status NOT IN ('Paid', 'Paused', 'Closed')""",
		as_dict=True)

def update_loan_record(doc):
	tbody, doc = [], get_loan_record(doc)

	doc.details = frappe.render_template("templates/loan_record_details.html", {
		"rows": get_doc(doc.meta.get_field("loan").options, doc.name).get("loan_schedule")
	})

  	doc.save()

def get_loan_record(doc):
	import fimax.utils

	doctype = "Loan Record"

	if not db.exists(doctype, doc.name):
		return fimax.utils.create_loan_record(doc)

	return get_doc(doctype, doc.name)
