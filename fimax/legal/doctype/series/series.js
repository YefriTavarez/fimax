// Copyright (c) 2018, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Series', {
	"onload": function(frm) {
		if (!frm.doc.creation) {
			frm.set_value("creation", frappe.datetime.now_datetime());
		}

		if (!frm.doc.owner) {
			frm.set_value("owner", frappe.session.user);
		}
	},
});
