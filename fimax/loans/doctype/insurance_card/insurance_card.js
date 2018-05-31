// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Insurance Card', {
	"refresh": (frm) => {	
	},
	"onload_post_render": (frm) => {
		if (frm.is_new()) {
			frm.trigger("start_date");
		}

		let fields = ["party", "party_type", "party_name", "company"];
		$.map(fields, (field)=> frm.add_fetch("loan", field, field));
	},
	"start_date": (frm) => {
		frm.set_value("end_date", frappe.datetime.add_months(frm.doc.start_date, 12));
	},
	"total_amount": (frm) => {
		events = ["calculate_pending_amount", "make_repayment_schedule"];
		$.map(events, (event) => frm.trigger(event));
	},
	"initial_payment_amount": (frm) => {
		frm.trigger("calculate_pending_amount");
		if (frm.doc.initial_payment_amount < 0.00) {
			let a_third_of_total_amt = frm.doc.total_amount * 0.3;
			
			frm.set_value("initial_payment_amount", a_third_of_total_amt);
			frappe.throw(__("Initial Payment Amount should be greater than zero!"));
		}
		frm.trigger("make_repayment_schedule");
	},
	"calculate_pending_amount": (frm) => {
		if (frm.doc.initial_payment_amount > frm.doc.total_amount) {
			frappe.msgprint(__("Initial Payment Amount can't be greater that Total Amount!"));
		}
			
		let pending_amount = frm.doc.total_amount - frm.doc.initial_payment_amount;
		frm.set_value("pending_amount", pending_amount);
	},
	"repayment_periods": (frm) => {
		let events = ["validate_repayment_periods", "make_repayment_schedule"];
		$.map(events, (event) => frm.trigger(event));
	},
	"validate_repayment_periods": (frm) => {
		if (frm.doc.repayment_periods <= 0.00) {
			frm.set_value("repayment_periods", 3.00);
			frappe.throw(__("Value for Repayment Periods should be greater than zero!"));
		}
	},
	"is_paid_upfront": (frm) => {
		frm.doc.insurance_repayment_schedule = [];
		frm.set_value("initial_payment_amount", frm.doc.total_amount);
	},
	"make_repayment_schedule": (frm) => {
		if (frm.doc.total_amount <= 0.00 || frm.doc.is_paid_upfront) { return ; }

		let monthly_insurance_amount = cint(frm.doc.pending_amount / frm.doc.repayment_periods);
		let pending_amount = frm.doc.pending_amount;
		let allocated_amount = 0.00;
		let row_idx = 1;

		frm.doc.insurance_repayment_schedule = [];
		let row;

		while (pending_amount >= monthly_insurance_amount) {
			row = frm.add_child("insurance_repayment_schedule", {
				"repayment_date": frappe.datetime.add_months(frm.doc.start_date, row_idx),
				"paid_amount": 0.00,
				"insurance_amount": monthly_insurance_amount,
				"pending_amount": monthly_insurance_amount,
				"status": "Pending"
			});

			pending_amount -= monthly_insurance_amount;
			allocated_amount += monthly_insurance_amount;
			row_idx ++;
		}

		real_pending_amount = frm.doc.pending_amount - allocated_amount;
		row.insurance_amount += real_pending_amount;
		row.pending_amount += real_pending_amount;

		frm.refresh_fields();
	}
});
