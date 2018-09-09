// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

$.map(["cur_prompt", "frappe.loan_charges_count"], 
	namespace => frappe.provide(namespace));

frappe.ui.form.on('Income Receipt', {
	"setup": frm => {
		frm.trigger("set_queries");
	},
	"refresh": frm => {
		if (!frm.is_new()) {
			frm.page.show_menu();
		}

		if (!frm.doc.docstatus && frm.doc.loan) {
			frm.trigger("add_loan_charges_button");
		}
	},
	"onload_post_render": frm => {
		frm.trigger("set_dynamic_labels");
	},
	"validate": frm => {
		let total_discount = 0;

		$.map(frm.doc.income_receipt_items, (row) => total_discount += row.discount);

		if (!frm.doc.write_off_amount == total_discount) {
			frappe.throw(__(`Total allocated discount should 
				be the same as the Write off amount!`));
		}
	},
	"set_queries": frm => {
		let queries = ["set_loan_query", "set_account_query", 
			"set_against_account_query", "set_income_account_query"];

		$.map(queries, query => frm.trigger(query));
	},
	"set_loan_query": frm => {
		frm.set_query("loan", {	"docstatus": "1" });
	},
	"set_account_query": frm => {
		frm.set_query("account", "income_receipt_items", () => {
			return {
				"filters": {
					"account_type": "Receivable",
					"company": frm.doc.company
				}
			};
		});
	},
	"set_against_account_query": frm => {
		frm.set_query("against_account", "income_receipt_items", () => {
			return {
				"filters": {
					"account_type": ["in", "Bank, Cash"],
					"company": frm.doc.company
				}
			};
		});
	},
	"set_income_account_query": frm => {
		frm.set_query("income_account", () => {
			return {
				"filters":  {
					"account_type": ["in", "Bank, Cash"],
					"company": frm.doc.company
				}
			};
		});
	},
	"loan": frm => {
		if (frm.doc.loan) {
			if (frm.is_new()) {
				$.map(["add_quick_entry_button", "count_loan_charges"], 
					event => frm.trigger(event));
			}

			$.map(["set_missing_values", "add_loan_charges_button"], 
				event => frm.trigger(event));
		} else {
			$.map(["clear_all_fields", "remove_loan_charges_button", "remove_quick_entry_button"], 
				event => frm.trigger(event));
		}
	},
	"count_loan_charges": frm => {
		$.map([
			"Capital", "Interest", "Repayment Amount",
			"Insurance", "Late Payment Fee", "GPS", "Recovery Expenses"
		], key => {
			frappe.db.get_value("Loan Charges", {
				"loan_charges_type": key,
				"loan": frm.doc.loan
			}, ["count(1) as records"], ({ records }) => {
				frappe.loan_charges_count[key] = records;
			});		
		});
	},
	"posting_date": frm => {
		if (!frm.doc.posting_date) {
			frm.set_value("loan", undefined);
		}

		if (frm.doc.loan) {
			frm.trigger("fetch_loan_charges");
		}
	},
	"write_off_amount": frm => {
		let income_receipt_items = frm.doc.income_receipt_items;
		let records = income_receipt_items.length;
		
		if (!records) { return ; }

		let row_discount = cint(frm.doc.write_off_amount / records);
		let remaining = frm.doc.write_off_amount - flt(row_discount * records);

		let idx = 0;
		$.each(income_receipt_items, (key, value) => {
			idx = key;
			value.discount = row_discount;
		});

		frm.doc.income_receipt_items[idx].discount += remaining;
		frm.refresh_fields();
	},
	"clear_all_fields": frm => {
		let except_list = ["posting_date"];

		$.map(frm.meta.fields, (field) => { 
			if (!["Section Break", "Column Break"].includes(field.fieldtype)) { 
				if (!except_list.includes(field.fieldname)) {
					frm.set_value(field.fieldname, undefined); 
				}
			}
		});
	},
	"set_missing_values": frm => {
		$.map(["fetch_loan_from_server"], event => frm.trigger(event));
	},
	"add_quick_entry_button": frm => {
		frappe.run_serially([
			() => frm.trigger("remove_quick_entry_button"),
			() => frm.add_custom_button(__("Quick Entry"), 
				event => frm.trigger("show_quick_entry"))
		]);
	},
	"add_loan_charges_button": frm => {
		frappe.run_serially([
			() => frappe.timeout(1),
			() => frm.add_custom_button(__("Loan Charges"), 
				event => frm.trigger("fetch_from_loan_charges"), __("Fetch From")),
			() => frm.page.set_inner_btn_group_as_primary(__("Fetch From"))
		]);
	},
	"remove_quick_entry_button": frm => {
		frm.remove_custom_button(__("Quick Entry"));
	},
	"remove_loan_charges_button": frm => {
		frm.remove_custom_button(__("Loan Charges"), __("Fetch From"));
	},
	"show_quick_entry": frm => {
		const fields = fimax.quick_entry.get_fields(frm),
			title = __("Quick Income Receipt"),

			primary_label = __("Apply Changes"),

			callback = (args) => {
				frm.call(method="apply_changes", args=args)
					.then(response => { 
						frm.refresh();
						frm.trigger("add_quick_entry_button");
					});
			};

		cur_prompt = frappe.prompt(fields, callback, title, primary_label);
		cur_prompt.has_primary_action = false;	
	},
	"fetch_loan_from_server": frm => {
		let doctype = "Loan";
		let docname = frm.doc.loan;

		if (docname) {
			frappe.provide(__("locals.{0}.{1}", [doctype, docname]));

			let request = {
			    "method": "fimax.api.get_loan"
			};
			
			request.args = {
				"doctype": doctype,
				"docname": docname
			};
			
			request.callback = response => {
				let doc = response.message
			
				if (doc) {
					doc.income_account_currency = doc.__onload["income_account_currency"];
					locals[doctype][docname] = doc;
				}

				frm.trigger("fillup_loan_dependant_fields");
			};
			
			frappe.call(request);
		}
	},
	"fetch_from_loan_charges": frm => {
		// fake fields in the form
		frm.fields_dict.loan_charges_type = {
			"df": frm.fields_dict.income_receipt_items.grid.fields_map.loan_charges_type
		};

		frm.fields_dict.repayment_period = {
			"df": frm.fields_dict.income_receipt_items.grid.fields_map.repayment_period
		};

		let d = new frappe.ui.form.MultiSelectDialog({
			"doctype": "Loan Charges",
			"target": frm,
			"date_field": "repayment_date",
			"setters": {
				"repayment_period": undefined,
				"loan_charges_type": undefined,
			},
			"get_query": () => {
				return {
					// "query": "fimax.queries.loan_charges_query",
					"filters": {
						"loan": frm.doc.loan,
						"status": ["not in", "Paid, Closed"],
						"docstatus": 1
					} 
				};
			},
			"action": (selections, args) => {
				d.dialog.hide();
				if (selections.length == 0) { return ; }

				fimax.utils.add_rows_to_income_receipt_table(frm, selections, args);
			}
		});

		
		let on_lct_change = function() {
			d.get_results();
		};

		frappe.run_serially([
			() => frappe.timeout(0.7),
			() => {
				let field = d.dialog.fields_dict.loan_charges_type;
				field.df.change = on_lct_change;
		
				d.dialog.has_primary_action = false;
			},
		]);
	},
	"fillup_loan_dependant_fields": frm => {

		let doc = frappe.get_doc("Loan", frm.doc.loan);

		if (!doc) { return ; }

		let field_list = {
			"company": "company", 
			"loan_currency": "currency", 
			"income_account_currency": "income_account_currency", 
			"mode_of_payment": "mode_of_payment", 
			"party_type": "party_type",
			"party": "party", 
			"party_name": "party_name"
		};

		$.each(field_list, (key, value) => {
			frm.set_value(key, doc[value]);
		});

		frm.trigger("fetch_loan_charges");
	},
	"company": frm => {
		frappe.db.get_value("Company", frm.doc.company, "default_currency")
			.then(({ message }) => {
				if (message) {
					frm.set_value("currency", message['default_currency']);
				}
			});
	},
	"fetch_loan_charges": frm => {
		frm.call("grab_loan_charges")
			.then(response => frm.trigger("set_dynamic_labels"));
	},
	"mode_of_payment": frm => {
		$.map(["set_default_income_account"],
			event => frm.trigger(event));
	},
	"show_hide_exchange_currency_field": frm => {
		frm.set_value("exchange_rate", 1.000);

		// compare loan currency with the cash / bank account currency
		frm.toggle_display("exchange_rate", 
			frm.doc.currency != frm.doc.income_account_currency);
	},
	"fetch_exchange_rates": frm => {
		let request = {
		    "method": "erpnext.setup.utils.get_exchange_rate"
		};
		
		request.args = {
			"from_currency": frm.doc.income_account_currency,
			"to_currency": frm.doc.currency,
			"transaction_date": frm.doc.posting_date
		};
		
		request.callback = function(response) {
			let exchange_rate = response.message
		
			if (exchange_rate) {
				frm.set_value("exchange_rate", exchange_rate);	
			}
		};
		
		frappe.call(request);
	},
	"update_income_receipt_items_with_mode_of_payment": frm => {
		$.map(frm.doc["income_receipt_items"], row => {
			row.mode_of_payment = frm.doc.mode_of_payment;
			row.against_account = frm.doc.income_account;
			row.against_account_currency = frm.doc.income_account_currency;
			row.against_exchange_rate = frm.doc.exchange_rate;
			row.allocated_amount = row.base_outstanding_amount / row.against_exchange_rate;
			row.base_allocated_amount = row.base_outstanding_amount;
			// row.party_exchange_rate = frm.doc.exchange_rate;
		});

		frm.refresh_fields();
	},
	"set_default_income_account": frm => {
		if (!frm.doc.mode_of_payment||!frm.doc.company) { return ; }

		frappe.db.get_value("Mode of Payment Account", {
			"parent": frm.doc.mode_of_payment,
			"company": frm.doc.company
		}, ["default_account"]).then((response) => {
			let data = response.message;

			if (!(data && data["default_account"])) {
				frappe.msgprint(repl(`Please set default Cash or Bank account in Mode of Payment 
					<a href="/desk#Form/Mode of Payment/%(mode_of_payment)s">%(mode_of_payment)s</a>
					for company %(company)s`, frm.doc));

				frm.set_value("mode_of_payment", undefined);
			} else {
				frm.set_value("income_account", data["default_account"]);
				frm.trigger("income_account");
			}
		});
	},
	"income_account": frm => {
		if (!frm.doc.income_account) { return ;	}

		frappe.db.get_value("Account", {
			"name": frm.doc.income_account,
		}, ["account_currency"])
			.then(response => {
				let data = response.message;

				if (data["account_currency"]) {
					frm.set_value("income_account_currency", data["account_currency"]);
				}
			}).then(response => frm.trigger("show_hide_exchange_currency_field"))
		.then(response => frm.trigger("fetch_exchange_rates"))
		.then(response => frm.trigger("update_income_receipt_items_with_mode_of_payment"))
	},
	"income_account_currency": frm => {
		if (frm.doc.income_account_currency) {
			frm.set_currency_labels(["allocated_amount"], 
				frm.doc.income_account_currency, "income_receipt_items");
		}
	},
	"exchange_rate": frm => {
		$.map(["update_income_receipt_items_with_mode_of_payment"],
			event => frm.trigger(event));
	},
	"calculate_totals": (frm, cdt, cdn) => {
		let total_paid = 0.000;
		let grand_total = 0.000;
		let total_outstanding = 0.000;

		$.map(frm.doc.income_receipt_items, (row) => {
			total_paid += flt(row.base_allocated_amount);
			grand_total += flt(row.base_total_amount);
			total_outstanding += flt(row.base_outstanding_amount);
		});

		frm.set_value("total_paid", total_paid); 
		frm.set_value("grand_total", grand_total); 
		frm.set_value("total_outstanding", total_outstanding); 
		frm.set_value("difference_amount", grand_total - total_paid); 
	},
	"set_dynamic_labels": (frm, cdt, cdn) => {
		
		// let dfs = frappe.utils.filter_dict(frappe.get_meta("Income Receipt Items").fields, {
		// 	"fieldname": "allocated_amount"
		// });
		
		frm.set_currency_labels(["total_paid", "grand_total",
			"total_outstanding", "difference_amount"], frm.doc.currency);
		frm.set_currency_labels(["write_off_amount"], frm.doc.loan_currency);

		let field_lists = [
			[["allocated_amount"], frm.doc.income_account_currency, 'income_receipt_items'],
			[["outstanding_amount", "total_amount", "discount"], frm.doc.loan_currency, 'income_receipt_items'],
			[["base_allocated_amount", "base_outstanding_amount", "base_total_amount"], frm.doc.currency, 'income_receipt_items'],
		];

		$.map(field_lists, d => frm.set_currency_labels(d[0], d[1], d[2]));
			
		frm.refresh_field("income_receipt_items");
	},
});

// include quick_income_receipt js file
{% include "fimax/loans/doctype/income_receipt/quick_income_receipt.js" %}

// include income_receipt_items js file
{% include "fimax/loans/doctype/income_receipt_items/income_receipt_items.js" %}
