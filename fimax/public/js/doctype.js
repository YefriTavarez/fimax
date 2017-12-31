// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on("DocType", {
	"onload_post_render": (frm) => {
		if (frm.is_new()) {
			frm.trigger("enable_custom_field");
		} else {
			frm.trigger("add_custom_buttons");
		}
	},
	"enable_custom_field": (frm) => {
		frm.toggle_enable("custom", "true");
	},
	"add_custom_buttons": (frm) => {
		let button_list = ["add_show_list_button"];

		$.map(button_list, (event) => {
			frm.trigger(event);
		});
	},
	"add_show_list_button": (frm) => {
		frm.add_custom_button("Show List", () => frm.trigger("show_doctype_list"));
	},
	"show_doctype_list": (frm) => {
		let view_type = "List";

		frappe.set_route(view_type, frm.docname);
	}
});