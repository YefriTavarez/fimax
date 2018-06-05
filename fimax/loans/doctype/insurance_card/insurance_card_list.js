frappe.listview_settings['Insurance Card'] = {
	"add_fields": ["status", "docstatus"],
	"get_indicator": (doc) => {
		let status_list = {
			"Active": "Active|green|status,=,Active",
			"Inactive": "Inactive|grey|status,=,Inactive",
			"Cancelled": "Cancelled|red|status,=,Cancelled",
		};

		return status_list[doc.status].split("|");
	}
}
