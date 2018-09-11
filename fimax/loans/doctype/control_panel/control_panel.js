// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Control Panel', {
	"onload": (frm) => {
		$.map(["set_queries"], event => frm.trigger(event));
	},
	"set_queries": (frm) => {
		$.map(["set_insurance_supplier_query", "set_gps_supplier_query"], event => frm.trigger(event));
	},
	"set_insurance_supplier_query": (frm) => {
		frm.set_query("insurance_supplier", {
			"supplier_type": __("Insurance Provider")
		});
	},
	"set_gps_supplier_query": (frm) => {
		frm.set_query("gps_supplier", {
			"supplier_type": __("GPS Provider")
		});

	},
});
