// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Insurance Card', {
	"onload": (frm) => {
		if (frm.is_new()) {
			frm.trigger("start_date");
		}

		$.each({
			"party": "party",
			"party_type": "party_type",
			"party_name": "party_name",
			"company": "company",
			"company_currency": "company_currency",
			"currency": "currency"
		}, (key, value)=> frm.add_fetch("loan", key, value));

		$.map(["set_status_indicators", "set_queries"], event => frm.trigger(event));
	},
	"set_queries": (frm) => {
		frm.set_query("loan", function() {
			return {
				"query": "fimax.queries.get_loans",
				"filters": {
					"asset_type": "Car",
					"docstatus": "1"
				}
			};
		});
	},
	"onload_post_render": (frm) => {
		frappe.realtime.on("real_progress", function(data) {
			frappe.show_progress(__("Wait"), flt(data.progress));

			if (cstr(data.progress) == "100") {
				frappe.run_serially([
					() => frappe.timeout(1),
					() => frappe.hide_progress()
				]);
			}
		});
	},
	"on_submit": (frm) => {
		frappe.run_serially([
			() => frappe.timeout(1.5),
			() => frm.trigger("save_initial_payment_receipt")
		]);
	},
	"save_initial_payment_receipt": (frm) => {
		frappe.new_doc("Income Receipt", {
			"loan": frm.doc.loan,
			"posting_date": frappe.datetime.now_date(),
			"user_remarks": __("Initial Payment for Insurance: {0}", [frm.docname]),
		}, () => {
			frappe.run_serially([
				() => frappe.timeout(1.5),
				() => cur_frm.save(),
			]);
		});
	},
	"start_date": (frm) => {
		frm.set_value("end_date", frappe.datetime.add_months(frm.doc.start_date, 12));
		frm.trigger("make_repayment_schedule");
	},
	"total_amount": (frm) => {
		events = ["calculate_outstanding_amount", "make_repayment_schedule"];
		$.map(events, (event) => frm.trigger(event));
	},
	"initial_payment_amount": (frm) => {
		frm.trigger("calculate_outstanding_amount");
		if (frm.doc.initial_payment_amount < 0.00) {
			let a_third_of_total_amt = frm.doc.total_amount * 0.3;
			
			frm.set_value("initial_payment_amount", a_third_of_total_amt);
			frappe.throw(__("Initial Payment Amount should be greater than zero!"));
		}
		frm.trigger("make_repayment_schedule");
	},
	"calculate_outstanding_amount": (frm) => {
		if (frm.doc.initial_payment_amount >= frm.doc.total_amount) {
			frappe.msgprint(__("Initial Payment Amount can't be greater or equals that Total Amount!"));
			frm.set_value("initial_payment_amount", 0.00);
		}
			
		let outstanding_amount = frm.doc.total_amount - frm.doc.initial_payment_amount;
		frm.set_value("outstanding_amount", outstanding_amount);
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

		let monthly_repayment_amount = cint(frm.doc.outstanding_amount / frm.doc.repayment_periods);
		let outstanding_amount = frm.doc.outstanding_amount;
		let allocated_amount = 0.00;
		let row_idx = 1;

		frm.doc.insurance_repayment_schedule = [];
		let row;

		while (outstanding_amount >= monthly_repayment_amount) {
			row = frm.add_child("insurance_repayment_schedule", {
				"repayment_date": frappe.datetime.add_months(frm.doc.start_date, row_idx),
				"paid_amount": 0.00,
				"repayment_amount": monthly_repayment_amount,
				"outstanding_amount": monthly_repayment_amount,
				"status": "Pending"
			});

			outstanding_amount -= monthly_repayment_amount;
			allocated_amount += monthly_repayment_amount;
			row_idx ++;
		}

		real_outstanding_amount = frm.doc.outstanding_amount - allocated_amount;
		row.repayment_amount += real_outstanding_amount;
		row.outstanding_amount += real_outstanding_amount;

		frm.trigger("set_status_indicators");
		frm.refresh_fields();
	},
	"set_status_indicators": (frm) => {
		let grid = frm.get_field('insurance_repayment_schedule').grid;

		grid.wrapper.find("div.rows .grid-row").each((idx, vhtml) => {
			let doc = frm.doc.insurance_repayment_schedule[idx];

			let html = $(vhtml);

			let indicator = {
				"Pending": "indicator orange",
				"Overdue": "indicator red",
				"Partially": "indicator yellow",
				"Paid": "indicator green",
			}[doc.status];

			// let's remove any previous set class
			$.map(["orange", "red", "yellow", "green"], (color) => {
				html.find("div[data-fieldname=status] .static-area.ellipsis")
					.removeClass(__("indicator {0}", [color]));
			});

			html.find("div[data-fieldname=status] .static-area.ellipsis").addClass(indicator);
		});
	},
	"sync_with_loan_charges": (frm) => {
		frm.call("sync_this_with_loan_charges")
			.then(() => frm.reload_doc());
	},
});
