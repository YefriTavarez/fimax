// Copyright (c) 2018, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Record', {
	refresh: function(frm) {
		frm.toggle_display("loan", true);
	}
});
