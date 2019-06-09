// Copyright (c) 2019, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

(function() {
	const { datetime, boot } = frappe,
	{ month_start, month_end } = datetime,
	{ sysdefaults } = boot;

	frappe.query_reports["Loan Charges"] = {
		"filters": [
			{
				"label": __("Company"),
				"fieldname": "company",
				"fieldtype": "Link",
				"default": sysdefaults["company"],
				"options": "Company",
				"reqd": true,
			},
			{
				"label": __("From Date"),
				"fieldname": "from_date",
				"fieldtype": "Date",
				"default": month_start(),
				"reqd": true,
			},
			{
				"label": __("To Date"),
				"fieldname": "to_date",
				"fieldtype": "Date",
				"default": month_end(),
				"reqd": true,
			},
			{
				"label": __("Party Type"),
				"fieldtype": "Select",
				"fieldname": "party_type",
				"options": [
					{ "label": __("Customer"), "value": "Customer" },
					{ "label": __("Employee"), "value": "Employee" },
					{ "label": __("Supplier"), "value": "Supplier" },
				],
				"default": "Customer",
				"change": event => {
					const {
						query_report,
						query_report_filters_by_name,
					} = frappe, {
						party_type,
					} = query_report_filters_by_name;

					let {
						party,
					} = query_report_filters_by_name;

					party.df.options = party_type
						.$input.val();

					query_report.refresh();
				},
			},
			{
				"label": __("Party"),
				"fieldtype": "Link",
				"fieldname": "party",
				"options": "Customer",
			},
			{
				"label": __("Loan"),
				"fieldname": "loan",
				"fieldtype": "Link",
				"options": "Loan",
			},
		]
	};
})();
