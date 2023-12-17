// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.listview_settings["Loan"] = {
	"add_fields": ["status", "docstatus"],
	"get_indicator": (doc) => {
		if (doc.status == "Open") {
			return [__("Open"), "red", "status,=,Open"];
		} else if (doc.status == "Disbursed") {
			return [__("Disbursed"), "blue", "status,=,Disbursed"];
		} else if (doc.status == "Recovered") {
			return [__("Recovered"), "orange", "status,=,Recovered"];
		} else if (doc.status == "Paused") {
			return [__("Paused"), "yellow", "status,=,Paused"];
		} else if (doc.status == "Closed") {
			return [__("Closed"), "green", "status,=,Closed"];
		} else if (doc.status == "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		}
	}
}
