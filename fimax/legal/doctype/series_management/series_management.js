// Copyright (c) 2018, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Series Management', {
	"setup": (frm) => {
		frm.disable_save();
	},
	"onload": (frm) => {
		frm.set_df_property("serie", "options", frm.doc.__onload.options);
	},
	"serie": (frm) => {
		frm.call("get_current")
			.then(() => frm.refresh_fields());
	}
});
