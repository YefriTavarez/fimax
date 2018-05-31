// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.listview_settings["Loan Charges"] = {
	"add_fields": ["status", "docstatus"],
	"hide_name_column": false,
	"get_indicator": (doc) => {
		let status_list = {
			"Pending": "Pending|orange|status,=,Pending",
			"Overdue": "Overdue|red|status,=,Overdue",
			"Partially": "Partially|yellow|status,=,Partially",
			"Closed": "Closed|blue|status,=,Closed",
			"Paid": "Paid|green|status,=,Paid",
		};

		return status_list[doc.status].split("|");
	}
};
