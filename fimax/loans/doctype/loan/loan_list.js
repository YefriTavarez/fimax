// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.listview_settings["Loan"] = {
	"add_fields": ["status", "docstatus"],
	"get_indicator": (doc) => {
		let status_list = {
			"Open": "Open|red|status,=,Open",
			"Disbursed": "Disbursed|blue|status,=,Disbursed",
			"Recovered": "Recovered|orange|status,=,Recovered",
			"Paused": "Paused|yellow|status,=,Paused",
			"Closed": "Closed|green|status,=,Closed",
			"Cancelled": "Cancelled|red|status,=,Cancelled",
		};

		return status_list[doc.status].split("|");
	}
}
