// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan_appl");
frappe.ui.form.on('Customer', {
	"refresh": (frm) => {
		frm.trigger("set_the_right_mask");
		//frm.trigger("set_defaults");
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
	"customer_name": (frm) => {
		frm.set_value("customer_name", frm.doc.customer_name.trim().toUpperCase());
	},
	"set_the_right_mask": (frm) => {
		let possible_mask_list = ["000-00000-0", "000-0000000-0"];

		$("input[data-fieldname=tax_id]")
			.unmask();

		$("input[data-fieldname=tax_id]")
			.mask(possible_mask_list[cint(frm.doc.tax_id_type) - 1]);
	},
	"set_defaults": (frm) => {
		if(frm.is_new())
			frm.set_value("tax_id_type", 2);
		frm.toggle_display("territory", false);
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

frappe.ui.form.on("Customer Job", {
	"company": (frm, cdt, cdn) => {
		let row = locals[cdt][cdn]; 
		frappe.model.set_value(cdt, cdn, "company", row.company.trim().toUpperCase());

	},
	"position": (frm, cdt, cdn) => {
		let row = locals[cdt][cdn]; 
		frappe.model.set_value(cdt, cdn, "position", row.position.trim().toUpperCase());

	},
	"company_phone": (frm, cdt, cdn) => {
		let row = locals[cdt][cdn]; 
		let mask_phone = "(000) 000-0000";
		$("input[data-fieldname=company_phone]").unmask();
		$("input[data-fieldname=company_phone]").mask(mask_phone);

	}
});

frappe.ui.form.on("Customer Reference", {
	"full_name": (frm, cdt, cdn) => {
		let row = locals[cdt][cdn]; 
		frappe.model.set_value(cdt, cdn, "full_name", row.full_name.trim().toUpperCase());

	},
	"address": (frm, cdt, cdn) => {
		let row = locals[cdt][cdn]; 
		frappe.model.set_value(cdt, cdn, "address", row.address.trim().toUpperCase());

	},
	"phone": (frm, cdt, cdn) => {
		let row = locals[cdt][cdn]; 
		let mask_phone = "(000) 000-0000";
		$("input[data-fieldname=phone]").unmask();
		$("input[data-fieldname=phone]").mask(mask_phone);

	}
});
