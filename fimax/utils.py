import frappe
from frappe.utils import add_to_date, cint, flt, nowdate
from erpnext.setup.utils import get_exchange_rate
from enum import Enum
from frappe import _

class DocStatus(Enum):
	DRAFT = 0
	SUBMITTED = 1
	CANCELLED = 2

def delete_doc(doc):
	if DocStatus(doc.docstatus) is DocStatus.SUBMITTED:
		doc.cancel()
	doc.delete()

def create_loan_record(doc):
	"""Creates a Loan Record given the Loan doc"""
	record = frappe.new_doc("Loan Record")

	record.update({
		"loan": doc.name,
		"status": doc.status,
		"party_type": doc.party_type,
		"party": doc.party
	})

	return record.insert(ignore_permissions=True)

def daily(date, idx):
    return add_to_date(date, days=cint(idx))

def weekly(date, idx):
    return add_to_date(date, days=cint(idx) * 7)

def biweekly(date, idx):
    return add_to_date(date, days=cint(idx) * 14)

def monthly(date, idx):
    return add_to_date(date, months=cint(idx))

def quartely(date, idx):
    return add_to_date(date, months=cint(idx) * 3)

def half_yearly(date, idx):
    return add_to_date(date, months=cint(idx) * 6)

def yearly(date, idx):
    return add_to_date(date, years=cint(idx))

def apply_changes_from_quick_income_receipt(doc, insurance_amount=.000, gps_amount=.000, capital_amount=.000, 
	interest_amount=.000, repayment_amount=.000, recovery_amount=.000, fine_amount=.000, total_amount=.000):
		# skip if the user didn't send any amount
		if not total_amount: return

		# clear the table
		doc.set("income_receipt_items", [])

		loan_charges_list = get_loan_charges_list(insurance_amount, gps_amount, capital_amount, 
			interest_amount, repayment_amount, recovery_amount, fine_amount)

		loan_doc = frappe.get_doc(doc.meta.get_field("loan").options, doc.loan)

		doc.income_account, doc.income_account_currency = doc.get_income_account_and_currency(loan_doc)

		doc.exchange_rate = get_exchange_rate(loan_doc.currency, doc.income_account_currency)
		doc.currency = frappe.get_value("Company", doc.company, "default_currency")
		
		for charge in doc.list_loan_charges(ignore_repayment_date=True):

			loan_charge = doc.get_income_receipt_item(loan_doc, charge)
			loan_charge.allocated_amount = 0.000

			# skip if there is not money for this loan charges type
			if not loan_charge.loan_charges_type in loan_charges_list:
				continue

			if charge.loan_charges_type == "Insurance" and insurance_amount:
				insurance_amount = get_new_amount(charge, loan_charge, insurance_amount)
				
			if charge.loan_charges_type == "Late Payment Fee" and fine_amount:
				fine_amount = get_new_amount(charge, loan_charge, fine_amount)
	
			if charge.loan_charges_type == "GPS" and gps_amount:
				gps_amount = get_new_amount(charge, loan_charge, gps_amount)
	
			if charge.loan_charges_type == "Capital" and capital_amount:
				capital_amount = get_new_amount(charge, loan_charge, capital_amount)
	
			if charge.loan_charges_type == "Interest" and interest_amount:
				interest_amount = get_new_amount(charge, loan_charge, interest_amount)
	
			if charge.loan_charges_type == "Repayment Amount" and repayment_amount:
				repayment_amount = get_new_amount(charge, loan_charge, repayment_amount)

			if charge.loan_charges_type == "Recovery Expenses" and recovery_amount:
				recovery_amount = get_new_amount(charge, loan_charge, recovery_amount)

			# skip for duplicates
			if not loan_charge.get("voucher_name") in [d.get("voucher_name") 
				for d in doc.income_receipt_items] and loan_charge.allocated_amount: 
				doc.append("income_receipt_items", loan_charge)

		total_unallocated = get_total_unallocated(insurance_amount, gps_amount, capital_amount, 
			interest_amount, repayment_amount, recovery_amount, fine_amount)

		if total_unallocated > 0.000:
			frappe.msgprint(_("""Warning: There is an unallocated balance of ${0}
				""".format(frappe.format_value(total_unallocated, df={"fieldtype": "Currency"}))))

		doc.calculate_totals()

def get_loan_charges_list(insurance_amount=.000, gps_amount=.000, capital_amount=.000, 
	interest_amount=.000, repayment_amount=.000, recovery_amount=.000, fine_amount=.000):
	"""Will return a list of the Loan Charges Types based on the parameters the user sent
		Posible values are: Capital, Interest, Repayment Amount,
			Insurance, Late Payment Fee, GPS
	"""
	loan_charges_list = []
	
	if insurance_amount:
		loan_charges_list.append("Insurance")
		
	if gps_amount:
		loan_charges_list.append("GPS")

	if capital_amount:
		loan_charges_list.append("Capital")

	if interest_amount:
		loan_charges_list.append("Interest")

	if repayment_amount:
		loan_charges_list.append("Repayment Amount")

	if recovery_amount:
		loan_charges_list.append("Recovery Expenses")

	if fine_amount:
		loan_charges_list.append("Late Payment Fee")

	return loan_charges_list

def get_new_amount(charge, loan_charge, allocated_amount):
	if allocated_amount < charge.outstanding_amount:
		loan_charge.allocated_amount = allocated_amount
		allocated_amount = .000
	else:
		loan_charge.allocated_amount = charge.outstanding_amount
		allocated_amount -= charge.outstanding_amount

	return allocated_amount

def get_total_unallocated(insurance_amount=.000, gps_amount=.000, capital_amount=.000, 
	interest_amount=.000, repayment_amount=.000, recovery_amount=.000, fine_amount=.000):
	return flt(insurance_amount) + flt(gps_amount) + flt(capital_amount) + flt(interest_amount)\
		+ flt(repayment_amount) + flt(recovery_amount) + flt(fine_amount)
