// Copyright (c) 2018, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Charges', {
	"setup": (frm) => {
		let event_list = ["set_queries"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"onload": (frm) => {
		if (!frm.is_new()) {
			frm.page.show_menu();
		}
	},
	"refresh": (frm) => {
		let event_list = ["set_dynamic_labels", "set_status_indicator"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"set_queries": (frm) => {
		let event_list = ["set_reference_name_query"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"set_dynamic_labels": (frm) => {
		let currency_fields = $.grep(frm.meta.fields, field => {
			if (field.fieldtype == "Currency") {
				return true;
			}

			return false;
		}).map(field => field.fieldname);

		frm.set_currency_labels(currency_fields, frm.doc.currency);
	},
	"set_status_indicator": (frm) => {
		frm.set_indicator_formatter("status", (doc) => {
			let colors = {
				"Pending": "orange",
				"Overdue": "red",
				"Partially": "yellow",
				"Closed": "blue",
				"Paid": "green",
			};

			return colors[doc.status] || "grey";
		}, (doc) => {
			return __(doc.status);
		});

		frm.refresh_fields();
	},
	"reference_type": (frm)  => {
		frm.trigger("clear_reference_name");
	},
	"clear_reference_name": (frm)  => {
		frm.set_value("reference_name", undefined);
	},
	"reference_name": (frm)  => {
		if (frm.doc.reference_name) {
			frm.trigger("validate_reference_name");
		}
	},
	"validate_reference_name": (frm)  => {
		frm.call("validate_reference_name")
			.fail(() => frm.trigger("clear_reference_name"));
	}
});
