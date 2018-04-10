// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan");
frappe.ui.form.on('Property', {
	"after_save": (frm) => {
		let url = fimax.loan.url;

		if (!url) {
			return 0;
		}

		frappe.model.set_value(url[1], url[2], "asset_type", frm.doctype);
		frappe.model.set_value(url[1], url[2], "asset", frm.docname);

		setTimeout(() => frappe.set_route(url), 500);

		delete fimax.loan.url;
	},
	"construction_year": (frm) => {
		if (!frm.doc.construction_year) {
			return 0;
		}

		let current_year = cint(frappe.datetime.get_today().split("-")[0]);
		
		if (frm.doc.construction_year <= current_year){
			let construction_age = current_year - frm.doc.construction_year;
			frm.set_value("construction_age", construction_age);
		} else{
			frappe.run_serially([
				() => frm.set_value("construction_age", undefined),
				() => frm.set_value("construction_year", undefined),
				() => frappe.throw(__("Construction year must be </br> greater or equal this year!"))
			]);
		}
	}
});
