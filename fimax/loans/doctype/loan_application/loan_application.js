// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan_appl");
frappe.ui.form.on('Loan Application', {
	"refresh": (frm) => {
		let event_list = ["set_queries", "add_fecthes",
			"update_interest_rate_label", "show_hide_party_name",
			"show_hide_fields_based_on_role", "add_custom_buttons"
		];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"onload": (frm) => {
		let event_list = ["set_approver", "set_defaults", "set_dynamic_labels"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"set_queries": (frm) => {
		let queries = ["set_party_type_query"];
		$.map(queries, (event) => frm.trigger(event));
	},
	"set_defaults": (frm) => {
		let queries = ["set_default_repayment_day"];
		$.map(queries, (event) => frm.trigger(event));
	},
	"set_dynamic_labels": (frm) => {
		$.map(frm.meta.fields, field => {
			if (field.fieldtype == "Currency") {
				let new_label = __("{0} ({1})", [field.label, frm.doc.currency]);
				frm.set_df_property(field.fieldname, "label", new_label);
			}
		});
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
			frm.doc.status != "Approved" && frm.page.set_inner_btn_group_as_primary(__("Action"));
		} else if (has_permission && frm.doc.docstatus == 1 && !allowed) {
			frappe.db.get_value("Loan", {
				"loan_application": frm.docname,
				"docstatus": ["!=", "2"]
			}, ["name"]).done((response) => {
				let data = response.message;

				if (!data) {
					frm.trigger("add_revoke_button");
				}
			});
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

		if (frm.is_new()) {
			let button_list = ["add_new_customer_button",
				"add_new_supplier_button", "add_new_employee_button"];
			$.map(button_list, (event) => frm.trigger(event));

			frm.page.set_inner_btn_group_as_primary(__("New"));
		}
	},
	"set_approver": (frm) => {
		if (frappe.user.has_role(["Loan Approver", "Loan Manager"])) {
			if (frm.doc.docstatus == 1 && !frm.doc.approver) {
				frm.doc.approver = frappe.session.user;
				frm.doc.approver_name = frappe.boot.user_info[frappe.session.user].fullname;
			}
		}
	},
	"set_queries": (frm) => {
		let queries = ["set_party_type_query"];
		$.map(queries, (event) => frm.trigger(event));
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
	"set_default_repayment_day": (frm) => {
		if (!frm.is_new()) {
			return 0;
		}

		let js_date = new Date();
		let day_of_the_month = js_date.getDate();

		if (day_of_the_month == 31) {
			day_of_the_month = 30;
		}

		frm.set_value("repayment_day_of_the_month", day_of_the_month);
	},
	"party_type": (frm) => {
		frm.trigger("clear_party") && frm.trigger("refresh");
	},
	"party": (frm) => {
		if (!frm.doc.party) {
			frm.trigger("clear_party_name");
		} else {
			frappe.run_serially([
				() => frappe.timeout(0.5),
				() => frm.trigger("set_party_name"),
				() => frm.trigger("set_party_currency")
			]);
		}
	},
	"currency": (frm) => {
		frm.trigger("set_dynamic_labels");
	},
	"set_party_name": (frm) => {
		let party_field = __("{0}_name", [frm.doc.party_type]);

		frappe.db.get_value(frm.doc.party_type, frm.doc.party, party_field.toLocaleLowerCase())
			.done((response) => {
				let data = response.message;
				let party_name = data && data[party_field.toLocaleLowerCase()];
				frm.set_value("party_name", party_name);
				frm.trigger("show_hide_party_name");
			}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party name!")));
	},
	"set_party_currency": (frm) => {
		let default_currency = frappe.defaults.get_default("currency");

		if (["Customer", "Supplier"].includes(frm.doc.party_type)) {
			frappe.db.get_value(frm.doc.party_type, frm.doc.party, "default_currency")
				.done((response) => {
					let data = response.message;
					default_currency = data && data["default_currency"];
					default_currency && frm.set_value("currency", default_currency);
				}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party default currency!")));
		}

		frm.set_value("currency", default_currency);
	},
	"clear_party": (frm) => {
		frappe.run_serially([
			() => frm.set_value("party", undefined),
			() => frm.trigger("clear_party_name")
		]);
	},
	"clear_party_name": (frm) => {
		frm.set_value("party_name", undefined);
	},
	"approver": (frm) => {
		if (!frm.doc.approver) {
			frm.set_value("approver_name", undefined);
		}
	},
	"loan_type": (frm) => {
		if (!frm.doc.loan_type) {
			return 0; // exit code is zero
		}

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
					// "repayment_day_of_the_month",
					"repayment_day_of_the_week",
					"repayment_days_after_cutoff",
					"repayment_frequency",
				], fieldname => frm.doc[fieldname] = loan_type[fieldname]);

				let repayment_interest_rate = flt(loan_type["interest_rate"]) /
					fimax.utils.frequency_in_years(frm.doc.repayment_frequency);

				frm.doc["interest_rate"] = repayment_interest_rate;
				frm.refresh_fields();
			});
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
	"approve_loan_appl": (frm) => {
		frm.doc.status = "Approved";
		frm.save("Update");
	},
	"deny_loan_appl": (frm) => {
		frm.doc.status = "Rejected";
		frm.save("Update");
	},
	"revoke_loan_appl": (frm) => {
		if (frm.doc.docstatus != 1) {
			frappe.throw(__("Can't revoke a non-validated Loan Application!"))
		}

		frappe.run_serially([
			() => frm.set_value("status", "Open"),
			() => frm.save("Update"),
		]);
	},
	"view_loan": (frm) => {
		frappe.db.get_value("Loan", {
			"loan_application": frm.docname,
			"docstatus": ["!=", "2"]
		}, "name").done((response) => {
			let loan = response.message["name"];

			if (loan) {
				frappe.set_route("Form", "Loan", loan);
			} else {
				frappe.msgprint(__("Loan not found"));
			}
		});
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
	},
	"new_customer": (frm) => {
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("party_type", "Customer"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Customer")
		]);
	},
	"new_supplier": (frm) => {
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("party_type", "Supplier"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Supplier")
		]);
	},
	"new_employee": (frm) => {
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("party_type", "Employee"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Employee")
		]);
	},
	"remember_current_route": (frm) => {
		fimax.loan_appl.url = frappe.get_route();
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
		let new_label = __("Interest Rate ({0})", [frm.doc.repayment_frequency]);
		frm.set_df_property("interest_rate", "label", new_label);
	},
	"add_approved_button": (frm) => {
		frm.add_custom_button(__("Approve"), () => frm.trigger("approve_loan_appl"), __("Action"));
	},
	"add_deny_button": (frm) => {
		frm.add_custom_button(__("Deny"), () => frm.trigger("deny_loan_appl"), __("Action"));
	},
	"add_revoke_button": (frm) => {
		frm.add_custom_button(__("Revoke"), () => frm.trigger("revoke_loan_appl"), __("Action"));
	},
	"add_make_loan_button": (frm) => {
		frm.add_custom_button(__("Make"), () => frm.trigger("make_loan"), __("Loan"));
	},
	"add_view_loan_button": (frm) => {
		frm.add_custom_button(__("View"), () => frm.trigger("view_loan"), __("Loan"));
	},
	"add_new_customer_button": (frm) => {
		frm.add_custom_button(__("Customer"), () => frm.trigger("new_customer"), __("New"));
	},
	"add_new_supplier_button": (frm) => {
		frm.add_custom_button(__("Supplier"), () => frm.trigger("new_supplier"), __("New"));
	},
	"add_new_employee_button": (frm) => {
		frm.add_custom_button(__("Employee"), () => frm.trigger("new_employee"), __("New"));
	},
	"show_hide_party_name": (frm) => {
		frm.toggle_display("party_name", frm.doc.party != frm.doc.party_name);
	},
	"show_hide_fields_based_on_role": (frm) => {
		if (frm.doc.docstatus == 1) {
			frm.toggle_enable("approved_gross_amount",
				frappe.user.has_role(["Loan Approver", "Loan Manager"]) && !["Approved", "Rejected"].includes(frm.doc.status));
		}

		$.map([
			"posting_date",
			"party_type", "party", "party_name",
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
		frm.call("validate").then(() => frm.refresh());
	},
	"calculate_loan_amount": (frm) => {
		let can_proceed = frm.doc.requested_gross_amount && frm.doc.legal_expenses_rate;

		if (can_proceed) {
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
			frm.doc.legal_expenses_amount = 0.000;
			frm.doc.approved_net_amount = 0.000;
		}

	},
	"calculate_legal_expenses_amount": (frm) => {
		frm.doc.legal_expenses_amount = flt(frm.doc.approved_gross_amount) 
			* fimax.utils.from_percent_to_decimal(frm.doc.legal_expenses_rate);

		refresh_field("legal_expenses_amount");
	},
	"calculate_requested_net_amount": (frm) => {
		frm.doc.requested_net_amount = flt(frm.doc.requested_gross_amount) 
			* flt(fimax.utils.from_percent_to_decimal(frm.doc.legal_expenses_rate) + 1);

		refresh_field("requested_net_amount");
	},
	"calculate_approved_net_amount": (frm) => {
		frm.doc.approved_net_amount = flt(frm.doc.legal_expenses_amount) + flt(frm.doc.approved_gross_amount);
		refresh_field("approved_net_amount");
	},
});
