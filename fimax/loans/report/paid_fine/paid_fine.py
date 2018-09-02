# Copyright (c) 2013, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	return [
		"LOAN:Link/Loan:120",
		"PARTY:Link/Customer:200",
		"REPAYMENT:INT:100",
		"FECHA:Date:120",
		"PAID AMOUNT:Currency:160",
		"TOTAL AMOUNT:Currency:160",
	]
def get_data(filters):
	result = frappe.db.sql("""
		SELECT 
			loan,
			party,
			repayment,
			fecha,
			paid_amount,
			total_amount
		FROM 
			`viewPaid Fine`
		WHERE 
			%(filters)s

	""" % { "filters": get_filters(filters) }, filters, debug=True)
	return result

def get_filters(filters):
	query = ["type = 'Late Payment Fee' AND status = 'Paid'"]

	if filters.get("loan"):
		query.append("loan = %(loan)s")

	if filters.get("party"):
		query.append("party = %(party)s")
	
	if filters.get("from_date"):
		query.append("fecha >= %(from_date)s")

	if filters.get("to_date"):
		query.append("fecha <= %(to_date)s")
	
	return " AND ".join(query)

def append_to_data(data, row):
	data.append({
		row.loan,
		row.party,
		row.repayment,
		row.fecha,
		row.paid_amount,
		row.total_amount,
	})