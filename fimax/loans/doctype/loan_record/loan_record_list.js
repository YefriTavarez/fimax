frappe.listview_settings["Loan Record"] = {
	"get_indicator": function(doc) {
		if (doc.status == "Open") {
			return [__("Open"), "red", "status,=,Open"];
		} else if (doc.status == "Disbursed") {
			return [__("Disbursed"), "blue", "status,=,Disbursed"];
		} else if (doc.status == "Recovered") {
			return [__("Recovered"), "gray", "status,=,Recovered"];
		} else if (doc.status == "Paused") {
			return [__("Paused"), "orange", "status,=,Paused"];
		} else if (doc.status == "Closed") {
			return [__("Closed"), "green", "status,=,Closed"];
		} else if (doc.status == "Legal") {
			return [__("Legal"), "red", "status,=,Legal"];
		} else if (doc.status == "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		}
	}
};