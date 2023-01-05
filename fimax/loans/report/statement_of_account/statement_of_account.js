// Copyright (c) 2022, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Statement of Account"] = {
	"filters": [
		{
			'fieldname':'from_date',
			'label':__('From Date'),
			'fieldtype': 'Date',
			'default': frappe.datetime.year_start()
		},
		{
			'fieldname':'to_date',
			'label':__('To Date'),
			'fieldtype': 'Date',
			'default': frappe.datetime.year_end()
		},
		{
			'fieldname':'customer_name',
			'label':__('Customer'),
			'fieldtype': 'Link',
			'options': 'Customer'
		},
		{
			'fieldname':'loan',
			'label':__('Loan'),
			'fieldtype': 'Link',
			'options': 'Loan'
		},
		// {
		// 	'fieldname':'status',
		// 	'label':__('Status'),
		// 	'fieldtype': 'Select',
		// 	'options': ['', 'Disbursed', 'Recovered', 'Paused', 'Closed', 'Legal'],
		// 	// 'default': 'Recovered',
		// },
		{
			'fieldname':'status',
			'label':__('Status'),
			'fieldtype': 'Select',
			'options': ['', 'Paid', 'Partially', 'Pending', 'Overdue'],
			'default': 'Overdue',
		},
		// {
		// 	'fieldname':'city',
		// 	'label':__('City'),
		// 	'fieldtype': 'Data',
		// },
	]
};
