// Copyright (c) 2018, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Charges', {
	"setup": (frm) => {
		let event_list = ["set_queries"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"set_queries": (frm) => {
		let event_list = ["set_reference_name_query"];
		$.map(event_list, (event) => frm.trigger(event));
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
