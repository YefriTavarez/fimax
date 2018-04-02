// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Insurance Card', {
	"refresh": (frm) => {

	},
	"onload": (frm) => {
		frm.is_new() && frm.trigger("start_date");
		//Let's add default Fetch for Party
		party_name = frm.doc.party_type.toLowerCase()+"_name";
		frm.add_fetch("party", party_name, "party_name");

	},
	"party_type": (frm) => {
		// Let's clean those fields first
		frm.set_value("party","");
		frm.set_value("party_name","");
		//then let's unfetch those fields
		frm.fetch_dict={}
		//Let's add a new fetch with the correct party
		party_name = frm.doc.party_type.toLowerCase()+"_name";
		frm.add_fetch("party", party_name, "party_name");

	},
	"party": (frm) => {
		if (!frm.doc.party){
			frm.set_value("party_name","");
			return
		}

	},
	"start_date": (frm) => {
		frm.set_value("end_date", frappe.datetime.add_months(frm.doc.start_date,12));
	},
	"total_amount": (frm) => {
		frm.trigger("calculate_pending_amount");
	},
	"initial_payment_amount": (frm) => {
		frm.trigger("calculate_pending_amount");
	},
	"calculate_pending_amount": (frm) => {
		if (frm.doc.initial_payment_amount > frm.doc.total_amount){
			frm.set_value("initial_payment_amount", 0.00);
			frappe.msgprint(__(" Initial Amount can't be Higher that Total amount!"));
		}
			
		frm.set_value("pending_amount", frm.doc.total_amount - frm.doc.initial_payment_amount);
	},
});
