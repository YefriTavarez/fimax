import frappe

def create_loan_charges_type(loan_charges_name, description=None, 
	repayment_frequency="Monthly", repayment_periods=1):
	return frappe.get_doc({
		"description": description,
		"doctype": "Loan Charges Type",
		"loan_charges_name": loan_charges_name,
		"repayment_frequency": repayment_frequency,
		"repayment_periods": repayment_periods
	})

