// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Property', {
	"refresh": (frm) => {

	},
	"construction_year": (frm) => {
		if (!frm.doc.construction_year)
			return;

		this_year = eval(frappe.datetime.get_today().split("-")[0]);
		
		if(frm.doc.construction_year <= this_year){
			frm.set_value("construction_age", this_year - frm.doc.construction_year);
		}
		else{
			frm.set_value("construction_age", undefined);
			frm.set_value("construction_year", undefined);
			frappe.show_alert(__("Construction year must be </br> greater or equal this year!"),5);
		}
	}
});
