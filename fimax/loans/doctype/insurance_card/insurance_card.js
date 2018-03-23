// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Insurance Card', {
	"refresh": (frm) => {

	},
	"onload": (frm) => {
		frm.is_new() && frm.trigger("start_date");
	},
	"start_date": (frm) => {
		frm.set_value("end_date", frappe.datetime.add_months(frm.doc.start_date,12));
	}
});
