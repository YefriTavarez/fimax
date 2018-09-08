// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Amortization Tool', {
	"refresh": (frm) => {
		let event_list = ["update_interest_rate_label",
			"add_custom_buttons"
		];

		$.map(event_list, (event) => frm.trigger(event));
	},
	"loan_type": (frm) => {
		if (!frm.doc.loan_type) { return 0; }

		frappe.db.get_value(frm.fields_dict.loan_type.df.options, frm.doc.loan_type, "*")
			.done((response) => {
				let loan_type = response.message;

				if (loan_type && !loan_type["enabled"]) {
					frappe.run_serially([
						() => frm.set_value("loan_type", undefined),
						() => frappe.throw(__("{0}: {1} is disabled.", [frm.fields_dict.loan_type.df.options, loan_type.loan_name]))
					]);
				}

				$.map([
					"currency",
					"interest_type",
					"legal_expenses_rate",
					"repayment_frequency",
				], fieldname => frm.doc[fieldname] = loan_type[fieldname]);

				let repayment_interest_rate = flt(loan_type["interest_rate"]) /
					fimax.utils.frequency_in_years(frm.doc.repayment_frequency);

				frm.doc["interest_rate"] = repayment_interest_rate;
				
				//let's update the label of repayment_frequency's field 
				frm.trigger("update_interest_rate_label");
				frm.refresh_fields();
			});
	},
	"add_custom_buttons": (frm) => {
		frm.add_custom_button(__("Clear"), () => frm.trigger("clear_form"));
		if(!frm.is_dirty()){
			frm.add_custom_button(__("Make Loan Application"), () => frm.trigger("make_loan_application"), __("Make"));
			frm.page.set_inner_btn_group_as_primary(__("Make"));
		}
	},
	"requested_gross_amount": (frm) => {
		if (frappe.session.user == frm.doc.owner) {
			frm.trigger("update_approved_gross_amount");
		}

		frm.trigger("calculate_loan_amount");
	},
	"approved_gross_amount": (frm) => {
		frappe.run_serially([
			() => frm.trigger("validate_approved_gross_amount"),
			() => frm.trigger("calculate_loan_amount")
		]);
	},
	"repayment_frequency": (frm) => {
		frappe.run_serially([
			() => frm.trigger("update_interest_rate"),
			() => frm.trigger("update_interest_rate_label"),
		]);
	}, 
	"repayment_periods": (frm) => {
		frappe.run_serially([
			() => frm.trigger("validate_repayment_periods"),
			() => frm.trigger("calculate_loan_amount")
		]);
	},
	"disbursement_date": (frm) => {
		if (frm.doc.disbursement_date) {
			frm.trigger("calculate_loan_amount");
		}
	},
	"legal_expenses_rate": (frm) => {
		if (frm.doc.legal_expenses_rate) {
			frm.trigger("calculate_loan_amount");
		}
	},
	"validate": (frm) => {
		$.map([
			"validate_legal_expenses_rate",
			"validate_requested_gross_amount",
			"validate_approved_gross_amount",
			"validate_repayment_periods",
		], (validation) => frm.trigger(validation));
	},
	"validate_repayment_periods": (frm) => {
		if (!frm.doc.repayment_periods) {
			frappe.throw(__("Missing Repayment Periods"));
		}
	},
	"validate_legal_expenses_rate": (frm) => {
		if (!frm.doc.legal_expenses_rate) {
			frappe.throw(__("Missing Legal Expenses Rate"));
		}
	},
	"validate_requested_gross_amount": (frm) => {
		if (!frm.doc.approved_gross_amount) {
			if (!frm.doc.requested_gross_amount) {
				frappe.throw(__("Missing Requested Gross Amount"));
			} else {
				frappe.throw(__("Missing Approved Gross Amount"));
			}
		}
	},
	"validate_approved_gross_amount": (frm) => {
		if (frm.doc.approved_gross_amount > frm.doc.requested_gross_amount) {
			frappe.throw(__("Approved Amount can not be greater than Requested Amount"));
		}
	},
	"update_interest_rate": (frm) => {
		if (!frm.doc.loan_type) {
			return 0;
		}

		frappe.db.get_value(frm.fields_dict.loan_type.df.options, frm.doc.loan_type, "interest_rate")
			.done((response) => {
				let data = response.message;

				if (data) {
					let repayment_interest_rate = flt(data["interest_rate"]) /
						fimax.utils.frequency_in_years(frm.doc.repayment_frequency);

					frm.set_value("interest_rate", repayment_interest_rate);
				} 
			});
	},
	"update_interest_rate_label": (frm) => {
		frm.set_currency_labels(["interest_rate"], __(frm.doc.repayment_frequency));
	},
	"show_hide_fields_based_on_role": (frm) => {

		$.map([
			"posting_date",
			"currency", "company",
			"requested_gross_amount",
			"legal_expenses_rate",
			"repayment_frequency", "repayment_periods",
			"interest_rate", "interest_type",
		], (field) => frm.toggle_enable(field, frappe.session.user == frm.doc.owner));
	},
	"update_approved_gross_amount": (frm) => {
		frm.set_value("approved_gross_amount", frm.doc.requested_gross_amount);
	},
	"interest_rate": (frm) => {
		if (!frm.doc.interest_rate) {
			frappe.throw(__("Missing Requested Gross Amount"));
		}

		if (!frm.doc.requested_gross_amount) {
			frappe.throw(__("Missing Interest Rate"));
		}

		if (!frm.doc.repayment_periods) {
			frappe.throw(__("Missing Repayment Periods"));
		}

		frm.trigger("update_repayment_amount");
	},
	"interest_type": (frm) => {
		if (frm.doc.interest_rate && frm.doc.requested_gross_amount && frm.doc.repayment_periods) {
			frm.trigger("update_repayment_amount");
		}
	},
	"update_repayment_amount": (frm) => {
		frm.call("validate").then(() => {
			frappe.run_serially([
				() => frm.refresh(),
				() => frm.dirty()
			]);
		});
	},
	"calculate_loan_amount": (frm) => {
		if (frm.doc.requested_gross_amount) {
			frappe.run_serially([
				() => frm.trigger("calculate_legal_expenses_amount"),
				() => frappe.timeout(0.5),
				() => frm.trigger("calculate_requested_net_amount"),
				() => frappe.timeout(0.5),
				() => frm.trigger("calculate_approved_net_amount"),
				() => frappe.timeout(0.5),
				() => {
					if (frm.doc.repayment_periods) {
						frm.trigger("update_repayment_amount")
					}
				}
			]);
		} else {
			frappe.msgprint(__("Invalid value for Requested Gross Amount!"));
			
			$.map(["legal_expenses_amount", "approved_net_amount"], fieldname => {
				frm.doc[fieldname] = 0.000;
			});
		}
	},
	"calculate_legal_expenses_amount": (frm) => {
		frm.doc.legal_expenses_amount = flt(frm.doc.approved_gross_amount) 
			* fimax.utils.from_percent_to_decimal(frm.doc.legal_expenses_rate);

		refresh_field("legal_expenses_amount");
	},
	"calculate_requested_net_amount": (frm) => {
		if (frm.doc.docstatus) { return ; }

		frm.doc.requested_net_amount = flt(frm.doc.requested_gross_amount) 
			* flt(fimax.utils.from_percent_to_decimal(frm.doc.legal_expenses_rate) + 1);

		refresh_field("requested_net_amount");
	},
	"calculate_approved_net_amount": (frm) => {
		frm.doc.approved_net_amount = flt(frm.doc.legal_expenses_amount) + flt(frm.doc.approved_gross_amount);
		refresh_field("approved_net_amount");
	},
	"clear_form": (frm) => {
		frm.make_new("Amortization Tool");
	},
	"make_loan_application": (frm) => {
		let opts = {
			"method": "fimax.api.create_loan_appl_from_tool"
		};

		opts.args = {
			"doc": frm.doc
		}

		frappe.call(opts).done(({ message }) => {
			let doc = frappe.model.sync(message)[0];
			frappe.set_route("Form", doc.doctype, doc.name);
		}).fail((exec) => frappe.msgprint(__("There was an error while creating the Loan Application")));
	},
});
