// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan_appl");
frappe.ui.form.on('Customer', {
	"refresh": (frm) => {
		frm.trigger("set_the_right_mask");
	},
	"onload": (frm) => {
		frm.set_df_property("tax_id_type", "options", [
			{"label": "RNC", "value": "1" },
			{"label": "Cedula", "value": "2" },
			{"label": "Pasaporte", "value": "3" }
		]);
	},
	"tax_id_type": (frm) => {
		if (!["1", "2", "3"].includes(frm.doc.tax_id_type)) {
			frappe.msgprint({
				"title": __("Value out of range"),
				"message": __("Tax ID Type must be one of: (RNC, Cedula, Pasaporte)"),
				"indicator": "red"
			});

			frm.set_value("tax_id_type", "1");
		} else if (frm.doc.tax_id_type == "3") {
			frappe.msgprint({
				"title": __("Feature not implemented"),
				"message": __("This feature is not implemented yet!"),
				"indicator": "red"
			});

 			frm.set_value("tax_id_type", "1");
		} else {
			frm.trigger("set_the_right_mask");

			frm.set_value("tax_id", undefined);
		}
	},
	"set_the_right_mask": (frm) => {
		let possible_mask_list = ["000-00000-0", "000-0000000-0"];

		$("input[data-fieldname=tax_id]")
			.unmask();

		$("input[data-fieldname=tax_id]")
			.mask(possible_mask_list[cint(frm.doc.tax_id_type) - 1]);
	},
	"after_save": (frm) => {
		let url = fimax.loan_appl.url;

		if (!url) {
			return 0;
		}

		frappe.model.set_value(url[1], url[2], "party_type", frm.doctype);
		frappe.model.set_value(url[1], url[2], "party", frm.docname);
		frappe.model.set_value(url[1], url[2], "party_name", frm.doc.customer_name);

		if (frm.doc.default_currency) {
			frappe.model.set_value(url[1], url[2], "currency", frm.doc.default_currency);
		}

		setTimeout(() => frappe.set_route(url), 500);

		delete fimax.loan_appl.url;
	}
});
