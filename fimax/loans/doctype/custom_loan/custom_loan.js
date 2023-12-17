// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Custom Loan', {
	"refresh": (frm) => {

	},
	"loan_name": (frm) => {
		frm.set_value("loan_name", frm.doc.loan_name.trim().toUpperCase());
	}
});
