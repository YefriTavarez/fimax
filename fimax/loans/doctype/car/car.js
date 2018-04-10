// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan");
frappe.ui.form.on('Car', {
	"after_save": (frm) => {
		let url = fimax.loan.url;

		if (!url) {
			return 0;
		}

		frappe.model.set_value(url[1], url[2], "asset_type", frm.doctype);
		frappe.model.set_value(url[1], url[2], "asset", frm.docname);

		setTimeout(() => frappe.set_route(url), 500);

		delete fimax.loan.url;
	}
});
