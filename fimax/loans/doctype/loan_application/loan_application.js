// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan_appl");
frappe.ui.form.on('Loan Application', {
	"refresh": (frm) => {
		frappe.run_serially([
			_ => frm.trigger("set_queries"),
			_ => frm.trigger("add_fecthes"),
			_ => frm.trigger("update_interest_rate_label"),
			_ => frm.trigger("show_hide_party_name"),
			_ => frm.trigger("show_hide_fields_based_on_role"),
			_ => frm.trigger("add_custom_buttons"),
		]);
	},
	"onload": (frm) => {
		frappe.run_serially([
			_ => frm.trigger("set_approver"),
			_ => frm.trigger("set_defaults"),
			_ => frm.trigger("set_dynamic_labels"),
		]);
	},
	"set_queries": (frm) => {
		frappe.run_serially([
			_ => frm.trigger("set_sales_invoice_query"),
			_ => frm.trigger("set_party_type_query"),
		]);
	},
	"set_defaults": (frm) => {
		frappe.run_serially([
			_ => frm.trigger("set_default_repayment_day"),
		]);
	},
	"set_dynamic_labels": (frm) => {
		const { doc, meta } = frm;
		let currency_fields = jQuery
			.grep(meta.fields, d => d.fieldtype === "Currency")
			.map(d => d.fieldname);

		frm.set_currency_labels(currency_fields, doc.currency);
	},
	"add_fecthes": (frm) => {
		frappe.run_serially([
			_ => frm.trigger("add_party_fetch"),
		]);
	},
	"add_custom_buttons": (frm) => {
		const { doc, page } = frm;

		let has_permission = frappe.user.has_role([
			"Loan Manager",
			"Loan Approver",
		]);

		let allow_to_change_action = frappe.boot.conf.allow_change_action;
		let allowed = allow_to_change_action || (doc.status === "Open" && doc.status != "Completed");

		if (has_permission && doc.docstatus == 1 && allowed) {
			frappe.run_serially([
				_ => frm.trigger("add_approved_button"),
				_ => frm.trigger("add_deny_button"),
			]);

			if (doc.status != "Approved") {
				page.set_inner_btn_group_as_primary(__("Actions"));
			}
		} else if (has_permission && doc.docstatus == 1 && !allowed) {
			frappe.db.get_value("Loan", {
				"loan_application": doc.name,
				"docstatus": ["!=", "2"]
			}, ["name"]).done((response) => {
				let data = response.message;

				if (!data) {
					frm.trigger("add_revoke_button");
				}
			});
		} else {
			frm.trigger("add_no_permission_button");
		}

		has_permission = frappe.user.has_role(["Loan Approver", "Loan Manager", "Loan User"]);
		if (doc.docstatus == 1 && doc.status == "Approved" && has_permission) {
			frappe.db.get_value("Loan", {
				"loan_application": doc.name,
				"docstatus": ["!=", "2"]
			}, ["name"]).done(({ message: data }) => {

				if (!jQuery.isEmptyObject(data)) {
					frm.trigger("add_view_loan_button");
					doc.loan = data.loan;
				} else {
					frm.trigger("add_make_loan_button");
				}

				frm.page.set_inner_btn_group_as_primary(__("Loan"));
			});
		}

		if (frm.is_new()) {
			frappe.run_serially([
				_ => frm.trigger("add_new_customer_button"),
				_ => frm.trigger("add_new_supplier_button"),
				_ => frm.trigger("add_new_employee_button"),
			]);

			frm.page.set_inner_btn_group_as_primary(__("New"));
		}
	},
	"set_approver": (frm) => {
		const { doc } = frm;

		if (frappe.user.has_role(["Loan Approver", "Loan Manager"])) {
			if (doc.docstatus == 1 && !doc.approver) {
				doc.approver = frappe.session.user;
				doc.approver_name = frappe.boot.user_info[frappe.session.user].fullname;
			}
		}
	},
	"set_sales_invoice_query": (frm) => {
		const { doc } = frm;

		if (doc.party_type !== "Customer") {
			return "ignore for non customers";
		}

		frm.set_query("sales_invoice", _ => {
			const filters = {
				"customer": doc.party,
				"docstatus": 1,
				"outstanding_amount": [">", 0],
			};

			return { filters };
		});
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

		//frm.set_value("repayment_day_of_the_month", day_of_the_month);
	},
	"party_type": (frm) => {
		const { doc } = frm;
		frm.trigger("clear_party") && frm.trigger("refresh");
	},
	"party": (frm) => {
		const { doc } = frm;
		if (!doc.party) {
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
		const { doc } = frm;
		frm.trigger("set_dynamic_labels");
	},
	"sales_invoice": (frm) => {
		const { doc } = frm;

		if (!doc.sales_invoice) {
			return "ignore for unset sales invoice";
		}

		const doctype = "Sales Invoice";
		const filters = {
			"name": doc.sales_invoice,
			"docstatus": 1
		};

		const fields = [
			"customer",
			"customer_name",
			"outstanding_amount",
			"currency",
		];

		frappe.db.get_value(doctype, filters, fields)
			.then(({ message: data }) => {
				if (data) {
					doc.party_type = "Customer";
					doc.party = data.customer;
					doc.party_name = data.customer_name;
					doc.currency = data.currency;
					doc.requested_gross_amount = data.outstanding_amount;
					doc.approved_gross_amount = data.outstanding_amount;
					doc.requested_net_amount = data.outstanding_amount;
					doc.approved_net_amount = data.outstanding_amount;
					frm.trigger("refresh");
				}
			});
	},
	"set_party_name": (frm) => {
		const { doc } = frm;
		let party_field = __("{0}_name", [doc.party_type]);

		frappe.db.get_value(doc.party_type, doc.party, party_field.toLocaleLowerCase())
			.done((response) => {
				let data = response.message;
				let party_name = data && data[party_field.toLocaleLowerCase()];
				frm.set_value("party_name", party_name);
				frm.trigger("show_hide_party_name");
			}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party name!")));
	},
	"set_party_currency": (frm) => {
		const { doc } = frm;
		let default_currency = frappe.defaults.get_default("currency");

		if (["Customer", "Supplier"].includes(doc.party_type)) {
			frappe.db.get_value(doc.party_type, doc.party, "default_currency")
				.done((response) => {
					let data = response.message;
					default_currency = data && data["default_currency"];
					default_currency && frm.set_value("currency", default_currency);
				}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party default currency!")));
		}

		frm.set_value("currency", default_currency);
	},
	"clear_party": (frm) => {
		const { doc } = frm;
		frappe.run_serially([
			() => frm.set_value("party", undefined),
			() => frm.trigger("clear_party_name")
		]);
	},
	"clear_party_name": (frm) => {
		const { doc } = frm;
		frm.set_value("party_name", undefined);
	},
	"approver": (frm) => {
		const { doc } = frm;
		if (!doc.approver) {
			frm.set_value("approver_name", undefined);
		}
	},
	"loan_type": (frm) => {
		const { doc } = frm;
		if (!doc.loan_type) {
			return 0; // exit code is zero
		}

		frappe.db.get_value(frm.fields_dict.loan_type.df.options, doc.loan_type, "*")
			.done((response) => {
				let loan_type = response.message;

				if (loan_type && !loan_type["enabled"]) {
					frappe.run_serially([
						() => frm.set_value("loan_type", undefined),
						() => frappe.throw(__("{0}: {1} is disabled.", [frm.fields_dict.loan_type.df.options, loan_type.loan_name]))
					]);
				}

				jQuery.map([
					"currency",
					"interest_type",
					"legal_expenses_rate",
					// "repayment_day_of_the_month",
					"repayment_day_of_the_week",
					"repayment_days_after_cutoff",
					"repayment_frequency",
				], fieldname => doc[fieldname] = loan_type[fieldname]);

				let repayment_interest_rate = flt(loan_type["interest_rate"]) /
					fimax.utils.frequency_in_years(doc.repayment_frequency);

				doc["interest_rate"] = repayment_interest_rate;

				// let's update the label of repayment_frequency's field 
				frm.trigger("update_interest_rate_label");
				frm.refresh_fields();
			});
	},
	"requested_gross_amount": (frm) => {
		const { doc } = frm;
		if (frappe.session.user == doc.owner) {
			frm.trigger("update_approved_gross_amount");
		}

		frm.trigger("calculate_loan_amount");
	},
	"approved_gross_amount": (frm) => {
		const { doc } = frm;
		frappe.run_serially([
			() => frm.trigger("validate_approved_gross_amount"),
			() => frm.trigger("calculate_loan_amount")
		]);
	},
	"repayment_frequency": (frm) => {
		const { doc } = frm;
		frappe.run_serially([
			() => frm.trigger("update_interest_rate"),
			() => frm.trigger("update_interest_rate_label"),
		]);
	},
	"repayment_periods": (frm) => {
		const { doc } = frm;
		frappe.run_serially([
			() => frm.trigger("validate_repayment_periods"),
			() => frm.trigger("calculate_loan_amount")
		]);
	},
	"legal_expenses_rate": (frm) => {
		const { doc } = frm;
		if (doc.legal_expenses_rate) {
			frm.trigger("calculate_loan_amount");
		}
	},
	"validate": (frm) => {
		const { doc } = frm;
		jQuery.map([
			"validate_legal_expenses_rate",
			// "validate_requested_gross_amount",
			"validate_approved_gross_amount",
			"validate_repayment_periods",
		], (validation) => frm.trigger(validation));
	},
	"validate_repayment_periods": (frm) => {
		const { doc } = frm;
		if (!doc.repayment_periods) {
			frappe.throw(__("Missing Repayment Periods"));
		}
	},
	"validate_legal_expenses_rate": (frm) => {
		const { doc } = frm;
		if (!doc.legal_expenses_rate) {
			frappe.throw(__("Missing Legal Expenses Rate"));
		}
	},
	"validate_requested_gross_amount": (frm) => {
		const { doc } = frm;

		if (!doc.approved_gross_amount) {
			if (!doc.requested_gross_amount) {
				frappe.throw(__("Missing Requested Gross Amount"));
			} else {
				frappe.throw(__("Missing Approved Gross Amount"));
			}
		}
	},
	"validate_approved_gross_amount": (frm) => {
		const { doc } = frm;
		if (doc.approved_gross_amount > doc.requested_gross_amount) {
			frappe.throw(__("Approved Amount can not be greater than Requested Amount"));
		}
	},
	"approve_loan_appl": (frm) => {
		const { doc } = frm;
		doc.status = "Approved";
		frm.save("Update");
	},
	"deny_loan_appl": (frm) => {
		const { doc } = frm;
		doc.status = "Rejected";
		frm.save("Update");
	},
	"revoke_loan_appl": (frm) => {
		const { doc } = frm;
		if (doc.docstatus != 1) {
			frappe.throw(__("Can't revoke a non-validated Loan Application!"))
		}

		frappe.run_serially([
			() => frm.set_value("status", "Open"),
			() => frm.save("Update"),
		]);
	},
	"view_loan": (frm) => {
		const { doc } = frm;
		frappe.db.get_value("Loan", {
			"loan_application": doc.name,
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
		const { doc } = frm;
		let opts = {
			"method": "fimax.api.create_loan_from_appl"
		};

		opts.args = {
			"doc": doc
		}

		frappe.call(opts).done((response) => {
			let doc = response.message;

			doc = frappe.model.sync(doc)[0];
			frappe.set_route("Form", doc.doctype, doc.name);
		}).fail((exec) => frappe.msgprint(__("There was an error while creating the Loan")));
	},
	"new_customer": (frm) => {
		const { doc } = frm;
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("party_type", "Customer"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Customer")
		]);
	},
	"new_supplier": (frm) => {
		const { doc } = frm;
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("party_type", "Supplier"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Supplier")
		]);
	},
	"new_employee": (frm) => {
		const { doc } = frm;
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("party_type", "Employee"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Employee")
		]);
	},
	"remember_current_route": (frm) => {
		const { doc } = frm;
		fimax.loan_appl.url = frappe.get_route();
	},
	"update_interest_rate": (frm) => {
		const { doc } = frm;
		if (!doc.loan_type) {
			return 0;
		}

		frappe.db.get_value(frm.fields_dict.loan_type.df.options, doc.loan_type, "interest_rate")
			.done((response) => {
				let data = response.message;

				if (data) {
					let repayment_interest_rate = flt(data["interest_rate"]) /
						fimax.utils.frequency_in_years(doc.repayment_frequency);

					frm.set_value("interest_rate", repayment_interest_rate);
				}
			});
	},
	"update_interest_rate_label": (frm) => {
		const { doc } = frm;
		frm.set_currency_labels(["interest_rate"], __(doc.repayment_frequency));
	},
	"add_approved_button": (frm) => {
		const { doc } = frm;
		frm.add_custom_button(__("Approve"), () => frm.trigger("approve_loan_appl"), __("Actions"));
	},
	"add_deny_button": (frm) => {
		frm.add_custom_button(__("Deny"), () => frm.trigger("deny_loan_appl"), __("Actions"));
	},
	"add_revoke_button": (frm) => {
		frm.add_custom_button(__("Revoke"), () => frm.trigger("revoke_loan_appl"), __("Actions"));
	},
	"add_no_permission_button": (frm) => {
		frm.add_custom_button(__("Not Permitted"), () => {
			frappe.msgprint(__("You need to be a Loan User or Loan Manager to perform any action"));
		}, __("Actions"));
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
		const { doc } = frm;
		frm.toggle_display("party_name", doc.party != doc.party_name);
	},
	"show_hide_fields_based_on_role": (frm) => {
		const { doc } = frm;
		if (doc.docstatus == 1) {
			frm.toggle_enable("approved_gross_amount",
				frappe.user.has_role(["Loan Approver", "Loan Manager"]) && !["Approved", "Rejected"].includes(doc.status));
		}

		jQuery.map([
			"posting_date",
			"party_type", "party", "party_name",
			"currency", "company",
			"requested_gross_amount",
			"legal_expenses_rate",
			"repayment_frequency", "repayment_periods",
			"interest_rate", "interest_type",
		], (field) => frm.toggle_enable(field, frappe.session.user == doc.owner));
	},
	"update_approved_gross_amount": (frm) => {
		const { doc } = frm;
		frm.set_value("approved_gross_amount", doc.requested_gross_amount);
	},
	"interest_rate": (frm) => {
		const { doc } = frm;
		if (!doc.interest_rate) {
			frappe.throw(__("Missing Requested Gross Amount"));
		}

		if (!doc.requested_gross_amount) {
			frappe.throw(__("Missing Interest Rate"));
		}

		if (!doc.repayment_periods) {
			frappe.throw(__("Missing Repayment Periods"));
		}

		frm.trigger("update_repayment_amount");
	},
	"interest_type": (frm) => {
		const { doc } = frm;
		if (doc.interest_rate && doc.requested_gross_amount && doc.repayment_periods) {
			frm.trigger("update_repayment_amount");
		}
	},
	"update_repayment_amount": (frm) => {
		const { doc } = frm;
		frm.call("validate").then(() => {
			frappe.run_serially([
				() => frm.refresh(),
				() => frm.dirty()
			]);
		});
	},
	"calculate_loan_amount": (frm) => {
		const { doc } = frm;
		let can_proceed = doc.requested_gross_amount && doc.legal_expenses_rate;

		if (can_proceed) {
			frappe.run_serially([
				() => frm.trigger("calculate_legal_expenses_amount"),
				() => frappe.timeout(0.5),
				() => frm.trigger("calculate_requested_net_amount"),
				() => frappe.timeout(0.5),
				() => frm.trigger("calculate_approved_net_amount"),
				() => frappe.timeout(0.5),
				() => {
					if (doc.repayment_periods) {
						frm.trigger("update_repayment_amount")
					}
				}
			]);
		} else {
			doc.legal_expenses_amount = 0.000;
			doc.approved_net_amount = 0.000;
		}

	},
	"calculate_legal_expenses_amount": (frm) => {
		const { doc } = frm;
		doc.legal_expenses_amount = flt(doc.approved_gross_amount)
			* fimax.utils.from_percent_to_decimal(doc.legal_expenses_rate);

		refresh_field("legal_expenses_amount");
	},
	"calculate_requested_net_amount": (frm) => {
		const { doc } = frm;
		if (doc.docstatus) { return; }

		doc.requested_net_amount = flt(doc.requested_gross_amount)
			* flt(fimax.utils.from_percent_to_decimal(doc.legal_expenses_rate) + 1);

		refresh_field("requested_net_amount");
	},
	"calculate_approved_net_amount": (frm) => {
		const { doc } = frm;
		doc.approved_net_amount = flt(doc.legal_expenses_amount) + flt(doc.approved_gross_amount);
		refresh_field("approved_net_amount");
	},
});
