// Copyright (c) 2016, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Paid Fine"] = {
	"filters": [
		{
			"label": "Loan",
			"fieldname": "loan",
			"fieldtype": "Link",
			"options": "Loan",
		},
		{
			"label": "Party",
			"fieldname": "party",
			"fieldtype": "Link",
			"options": "Customer",
		},
		{
			"label": "From Date",
			"fieldname": "from_date",
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
		},
		{
			"label": "To Date",
			"fieldname": "to_date",
			"fieldtype": "Date",
			"default": frappe.datetime.month_end(),
		}
	]
}
