// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Application', {
	"onload": (frm) => {
		let event_list = ["set_approver", "set_default_values"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"refresh": (frm) => {
		let event_list = ["set_queries", "add_fecthes", 
			"update_interest_rate_label", "show_hide_party_name",
			"show_hide_fields_based_on_role", "add_custom_buttons"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"set_approver": (frm) => {
		if (frappe.user.has_role(["Loan Approver", "Loan Manager"])) {
			if ( ! frm.doc.approver) {
				frm.doc.approver = frappe.session.user;
				frm.doc.approver_name = frappe.boot.user_info[frappe.session.user].fullname;
			}
		}
	},
	"set_default_values": (frm) => {
		let event_list = ["set_default_status", "set_default_repayment_frequency"];
		if (frm.is_new()) {
			$.map(event_list, (event) => frm.trigger(event));
		}
	},
	"set_default_status": (frm) => {
		frm.set_value("status", "Open");
	},
	"set_default_status": (frm) => {
		frm.set_value("repayment_frequency", frappe.boot.conf.repayment_frequency);
	},
	"set_queries": (frm) => {
		let queries = ["set_party_type_query"];
		$.map(queries, (event) => frm.trigger(event));
	}, 	
	"add_fecthes": (frm) => {
		let queries = ["add_party_fetch"];
		$.map(queries, (event) => frm.trigger(event));
	},
	"add_custom_buttons": (frm) => {
		let has_permission = frappe.user.has_role(["Loan Approver", "Loan Manager"]);
		let allow_to_change_action = frappe.boot.conf.allow_change_action;
		let allowed = allow_to_change_action || (frm.doc.status == "Open" && frm.doc.status != "Completed");

		if (has_permission && frm.doc.docstatus == 1 && allowed) {
			$.map(["add_approved_button", "add_deny_button"], (event) => frm.trigger(event));
			frm.doc.status != "Approved" &&	frm.page.set_inner_btn_group_as_primary(__("Action"));
		}

		has_permission = frappe.user.has_role(["Loan Approver", "Loan Manager", "Loan User"]);
		if (frm.doc.docstatus == 1 && frm.doc.status == "Approved" && has_permission) {
			frappe.db.get_value("Loan", {
				"loan_application": frm.docname,
				"docstatus": ["!=", "2"]
			}, ["name"]).done((response) => {
				let data = response.message;

				if (data) {
					frm.trigger("add_view_loan_button");
					frm.doc.loan = data.loan;
				} else {
					frm.trigger("add_make_loan_button");
				}

				frm.page.set_inner_btn_group_as_primary(__("Loan"));
			});
		}
	},
	"set_party_type_query": (frm) => {
		frm.set_query("party_type", () => {
			return {
				"filters": {
					"name": ["in", ["Supplier", "Customer", "Employee"]]
				}
			};
		});
	},
	"party_type": (frm) => {
		$.map(["party", "party_name"], (field) => {
			frm.doc[field] = undefined;
			refresh_field(field);
		});
	},
	"party": (frm) => {
		if ( ! frm.doc.party) {
			frm.set_value("party_name", undefined);
		}

		let party_field = __("{0}_name", [frm.doc.party_type]);

		frappe.db.get_value(frm.doc.party_type, frm.doc.party, party_field.toLocaleLowerCase())
			.done((response) => {
				let party_name = response.message[party_field.toLocaleLowerCase()];
				frm.set_value("party_name", party_name);
				frm.trigger("show_hide_party_name");
			}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party name!")));
	},
	"approver": (frm) => {
		if ( ! frm.doc.approver) {
			frm.set_value("approver_name", undefined);
		}
	},
	"requested_gross_amount": (frm) => {
		if (frm.doc.owner == frappe.session.user) {
			frm.trigger("update_approved_gross_amount");
		}

		frm.trigger("calculate_loan_amount")
	},
	"legal_expenses_rate": (frm) => frm.trigger("calculate_loan_amount"),
	"approved_gross_amount": (frm) => frm.trigger("calculate_loan_amount"),
	"repayment_frequency": (frm) => frm.trigger("update_interest_rate_label"),
	"update_interest_rate_label": (frm) => {
		let new_label = __("Interest Rate ({0})", [frm.doc.repayment_frequency]);
		frm.set_df_property("interest_rate", "label", new_label);
	},
	"add_approved_button": (frm) => {
		frm.add_custom_button(__("Approve"), () => frm.trigger("approve_loan_appl"), __("Action"));
	},
	"add_deny_button": (frm) => {
		frm.add_custom_button("Deny", () => frm.trigger("deny_loan_appl"), __("Action"));
	},
	"add_make_loan_button": (frm) => {
		frm.add_custom_button("Make", () => frm.trigger("make_loan"), __("Loan"));
	},
	"add_view_loan_button": (frm) => {
		frm.add_custom_button("View", () => frm.trigger("view_loan"), __("Loan"));
	},
	"show_hide_party_name": (frm) => {
		frm.toggle_display("party_name", frm.doc.party != frm.doc.party_name);
	},
	"show_hide_fields_based_on_role": (frm) => {
		$.map(["approved_gross_amount"], 
			(field) => frm.toggle_enable(field, !! frappe.user.has_role(["Loan Approver", "Loan Manager"])));

		$.map([
			"posting_date",
			"party_type",
			"party",
			"party_name",
			"currency",
			"company",
			"requested_gross_amount",
			"legal_expenses_rate",
			"repayment_frequency",
			"repayment_periods",
			"interest_rate",
			"interest_type",
		], 
			(field) => frm.toggle_enable(field, frappe.session.user == frm.doc.owner));
	},
	"validate": (frm) => {
		$.map([
			"validate_legal_expenses_rate",
			"validate_requested_gross_amount",
			"validate_repayment_periods",
		], (validation) => frm.trigger(validation));
	},
	"calculate_loan_amount": (frm) => {
		let can_proceed = frm.doc.requested_gross_amount 
			&& frm.doc.legal_expenses_rate && frm.doc.repayment_periods;
		
		if (can_proceed) {
			frappe.run_serially([
				() => frm.trigger("calculate_legal_expenses_amount"),
				() => frm.trigger("calculate_requested_net_amount"),
				() => frm.trigger("calculate_approved_net_amount"),
			]);
		} else {
			frm.doc.legal_expenses_amount = 0.000;
			frm.doc.requested_gross_amount = 0.000;
			frm.doc.approved_net_amount = 0.000;
		}
	},		
	"calculate_legal_expenses_amount": (frm) => {
		frm.doc.legal_expenses_amount = flt(frm.doc.approved_gross_amount)
			* fimax.utils.from_percent_to_decimal(frm.doc.legal_expenses_rate);
		refresh_field("legal_expenses_amount");
	},
	"calculate_requested_net_amount": (frm) => {
		frm.doc.requested_net_amount = flt(frm.doc.legal_expenses_amount) 
			+ flt(frm.doc.requested_gross_amount);
		refresh_field("requested_net_amount");
	},
	"calculate_approved_net_amount": (frm) => {
		frm.doc.approved_net_amount = flt(frm.doc.legal_expenses_amount) 
			+ flt(frm.doc.approved_gross_amount);
		refresh_field("approved_net_amount");
	},
	"update_approved_gross_amount": (frm) => {
		frm.set_value("approved_gross_amount", frm.doc.requested_gross_amount);
	},
	"validate_legal_expenses_rate": (frm) => {
		if ( ! frm.doc.legal_expenses_rate) {
			frappe.throw(__("Missing Legal Expenses Rate"));
		}
	},
	"validate_requested_gross_amount": (frm) => {
		if ( ! frm.doc.approved_gross_amount) {
			if ( ! frm.doc.requested_gross_amount) {
				frappe.throw(__("Missing Requested Gross Amount"));
			} else {
				frappe.throw(__("Missing Approved Gross Amount"));
			}
		}
	},
	"validate_repayment_periods": (frm) => {
		if ( ! frm.doc.repayment_periods) {
			frappe.throw(__("Missing Repayment Periods"));
		}
	}, 
	"approve_loan_appl": (frm) => {
		frm.doc.status = "Approved";
		frm.save("Update");
	},
	"deny_loan_appl": (frm) => {
		frm.doc.status = "Rejected";
		frm.save("Update");
	},
	"view_loan": (frm) => {
		if (frm.doc.loan) {
			frappe.set_route("Form", "Loan", frm.doc.loan);
		} else {
			frappe.msgprint(__("Loan not found"));
		}
	},
	"make_loan": (frm) => {
		let opts = {
			"method": "fimax.api.create_loan_from_appl"
		};

		opts.args = {
			"doc": frm.doc
		}

		frappe.call(opts).done((response) => {
			let doc = response.message;

			doc = frappe.model.sync(doc)[0];
			frappe.set_route("Form", doc.doctype, doc.name);
		}).fail((exec) => frappe.msgprint(__("There was an error while creating the Loan")));
	}
});
