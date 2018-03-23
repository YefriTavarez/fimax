// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee', {
	"after_save": (frm) => {
		if (fimax.loan_appl.url) {
			frappe.model.set_value(fimax.loan_appl.url[1], fimax.loan_appl.url[2], "party_type", frm.doctype);
			frappe.model.set_value(fimax.loan_appl.url[1], fimax.loan_appl.url[2], "party", frm.docname);
			frappe.model.set_value(fimax.loan_appl.url[1], fimax.loan_appl.url[2], "party_name", frm.doc.employee_name);
	
			frappe.set_route(fimax.loan_appl.url);

			delete fimax.loan_appl.url;
		}
	}
});
