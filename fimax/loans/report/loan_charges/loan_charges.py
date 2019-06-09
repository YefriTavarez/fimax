# Copyright (c) 2019, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	return get_columns(filters), \
		get_data(filters)

def get_columns(filters):

	return [
		__get_formatted_field("Name", fieldtype="Link", options="Loan Charges", width=80),
		__get_formatted_field("Status", fieldtype="Data", width=100),
		__get_formatted_field("Party", fieldtype="Data", width=120),
		__get_formatted_field("Loan", fieldtype="Link", options="Loan", width=80),
		__get_formatted_field("Repayment Date", fieldtype="Date", width=80),
		__get_formatted_field("Repayment Period", fieldtype="Int", width=80),
		__get_formatted_field("Loan Charges Type", fieldtype="Data", width=100),
		__get_formatted_field("Outstanding Amount", fieldtype="Currency", width=100),
		__get_formatted_field("Total Amount", fieldtype="Currency", width=100),
		__get_formatted_field("Paid Amount", fieldtype="Currency", width=100),
	]

def get_data(filters):
	from frappe import db, _

	conditions = get_conditions(filters)

	resultset = db.sql(
		"""
		Select
			`tabLoan Charges`.`name`,
			`tabLoan Charges`.`status`,
			`tabLoan`.`party`,
			`tabLoan Charges`.`loan`,
			`tabLoan Charges`.`repayment_date`,
			`tabLoan Charges`.`repayment_period`,
			`tabLoan Charges`.`loan_charges_type`,
			`tabLoan Charges`.`outstanding_amount`,
			`tabLoan Charges`.`total_amount`,
			`tabLoan Charges`.`paid_amount`
		From
			`tabLoan`
		Inner Join
			`tabLoan Charges`
			On
				`tabLoan Charges`.`loan` = `tabLoan`.`name`
		Where
			{conditions}
		""".format(conditions=conditions),
	filters, as_list=True)

	dataobject = list(resultset)

	for d in dataobject:
		# try to translate loan_charges_type
		d[6] = _(d[6])

	return dataobject

def get_conditions(filters):
	conditions = ["`tabLoan`.`docstatus` = 1"]

	if filters.get("company"):
		conditions = ["`tabLoan`.`company` = %(company)s"]

	if filters.get("from_date"):
		conditions = ["`tabLoan Charges`.`repayment_date` >= %(from_date)s"]

	if filters.get("to_date"):
		conditions = ["`tabLoan Charges`.`repayment_date` <= %(to_date)s"]

	if filters.get("loan"):
		conditions = ["`tabLoan Charges`.`loan` = %(loan)s"]

	if filters.get("status"):
		conditions = ["`tabLoan Charges`.`status` = %(status)s"]

	if filters.get("party_type"):
		conditions = ["`tabLoan`.`party_type` = %(party_type)s"]

	if filters.get("party"):
		conditions = ["`tabLoan`.`party` = %(party)s"]

	return " And ".join(conditions)

def __get_formatted_field(label, width=100, fieldtype="Data", options=""):
	from frappe import _

	return "{label}:{fieldtype}/{options}:{width}".format(label=_(label),
		width=width, fieldtype=fieldtype, options=options)
