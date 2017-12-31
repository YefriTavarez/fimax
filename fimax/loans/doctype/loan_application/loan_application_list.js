// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.listview_settings["Loan Application"] = {
	"add_fields": ["status", "docstatus"],
	"hide_name_column": true,
	"get_indicator": (doc) => {
		let status_list = {
			"Open": "Open|orange|status,=,Open",
			"Approved": "Approved|blue|status,=,Approved",
			"Completed": "Completed|green|status,=,Completed",
			"Rejected": "Rejected|red|status,=,Rejected",
		};

		return status_list[doc.status].split("|");
	}
}