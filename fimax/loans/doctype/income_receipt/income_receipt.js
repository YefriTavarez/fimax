// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Income Receipt', {
	"setup": (frm) => {
		frm.trigger("set_queries");
	},
	"refresh": (frm) => {
		if (!frm.is_new()) {
			frm.page.show_menu();
		}
	},
	"onload_post_render": (frm) => {
		frm.trigger("set_dynamic_labels");
	},
	"set_queries": (frm) => {
		let queries = ["set_loan_query", "set_account_query", 
			"set_against_account_query", "set_income_account_query"];

		$.map(queries, query => frm.trigger(query));
	},
	"set_loan_query": (frm) => {
		frm.set_query("loan", {	"docstatus": "1" });
	},
	"set_account_query": (frm) => {
		frm.set_query("account", "income_receipt_items", () => {
			return {
				"filters": {
					"account_type": "Receivable",
					"company": frm.doc.company
				}
			};
		});
	},
	"set_against_account_query": (frm) => {
		frm.set_query("against_account", "income_receipt_items", () => {
			return {
				"filters": {
					"account_type": ["in", "Bank, Cash"],
					"company": frm.doc.company
				}
			};
		});
	},
	"set_income_account_query": (frm) => {
		frm.set_query("income_account", () => {
			return {
				"filters":  {
					"account_type": ["in", "Bank, Cash"],
					"company": frm.doc.company
				}
			};
		});
	},
	"loan": (frm) => {
		if (frm.doc.loan) {
			frm.trigger("set_missing_values");
		} else {
			frm.trigger("clear_all_fields");
		}
	},
	"posting_date": (frm) => {
		if (!frm.doc.posting_date) {
			frm.set_value("loan", undefined);
		}

		if (frm.doc.loan) {
			frm.trigger("fetch_loan_charges");
		}
	},
	"clear_all_fields": (frm) => {
		let except_list = ["posting_date"];

		$.map(frm.meta.fields, (field) => { 
			if (!["Section Break", "Column Break"].includes(field.fieldtype)) { 
				if (!except_list.includes(field.fieldname)) {
					frm.set_value(field.fieldname, undefined); 
				}
			}
		});
	},
	"set_missing_values": (frm) => {
		$.map(["fetch_loan_from_server"], (event) => frm.trigger(event));
	},
	"fetch_loan_from_server": (frm) => {
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
	"fillup_loan_dependant_fields": (frm) => {

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
	"company": (frm) => {
		frappe.db.get_value("Company", frm.doc.company, "default_currency")
			.then(response => {
				let data = response.message;
				if (data) {
					frm.set_value("currency", data['default_currency']);
				}
			});
	},
	"fetch_loan_charges": (frm) => {
		frm.call("grab_loan_charges")
			.then(() => frm.trigger("set_dynamic_labels"));
	},
	"mode_of_payment": (frm) => {
		$.map(["set_default_income_account"],
			(event) => frm.trigger(event));
	},
	"show_hide_exchange_currency_field": (frm) => {
		frm.set_value("exchange_rate", 1.000);

		// compare loan currency with the cash / bank account currency
		frm.toggle_display("exchange_rate", 
			frm.doc.currency != frm.doc.income_account_currency);
	},
	"fetch_exchange_rates": (frm) => {
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
	"update_income_receipt_items_with_mode_of_payment": (frm) => {
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
	"set_default_income_account": (frm) => {
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
	"income_account": (frm) => {
		if (!frm.doc.income_account) { return ;	}

		frappe.db.get_value("Account", {
			"name": frm.doc.income_account,
		}, ["account_currency"])
			.then(response => {
				let data = response.message;

				if (data["account_currency"]) {
					frm.set_value("income_account_currency", data["account_currency"]);
				}
			}).then(() => frm.trigger("show_hide_exchange_currency_field"))
		.then(() => frm.trigger("fetch_exchange_rates"))
		.then(() => frm.trigger("update_income_receipt_items_with_mode_of_payment"))
	},
	"income_account_currency": (frm) => {
		if (frm.doc.income_account_currency) {
			frm.set_currency_labels(["allocated_amount"], 
				frm.doc.income_account_currency, "income_receipt_items");
		}
	},
	"exchange_rate": (frm) => {
		$.map(["update_income_receipt_items_with_mode_of_payment"],
			(event) => frm.trigger(event));
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

		let field_lists = [
			[["allocated_amount"], frm.doc.income_account_currency, 'income_receipt_items'],
			[["outstanding_amount", "total_amount"], frm.doc.loan_currency, 'income_receipt_items'],
			[["base_allocated_amount", "base_outstanding_amount", "base_total_amount"], frm.doc.currency, 'income_receipt_items'],
		];

		$.map(field_lists, d => frm.set_currency_labels(d[0], d[1], d[2]));
			
		frm.refresh_field("income_receipt_items");
	},
});

frappe.ui.form.on('Income Receipt Items', {
	"before_income_receipt_items_remove": (frm, cdt, cdn) => {
		frappe.throw(__("Ajaah!"));
	},
	"income_receipt_items_add": (frm, cdt, cdn) => {
		if (frm.doc.income_account) {
			frappe.model.set_value(cdt, cdn, "against_account", frm.doc.income_account);
		}
	},
	"against_account": (frm, cdt, cdn) => {
		let doc = frappe.get_doc(cdt, cdn);

		frappe.db.get_value("Account", {
			"name": doc.against_account 
		}, "account_currency").then((response) => {
			let data = response.message;

			if (data) {
				frappe.model.set_value(cdt, cdn, "against_account_currency", data.account_currency);
			}
			
			frm.trigger("set_dynamic_labels");
		});

		let field_lists = [
			[["allocated_amount"], doc.currency, "income_receipt_items"],
			[["outstanding_amount", "total_amount"], doc.currency, "income_receipt_items"],
		]; 

		$.map(field_lists, (d) => {
			frm.set_currency_labels(d[0], d[1], d[2]);
		});
	},
	"account": (frm, cdt, cdn) => {
		let doc = frappe.get_doc(cdt, cdn);

		frappe.db.get_value("Account", {
			"name": doc.account 
		}, "account_currency").then((response) => {
			let data = response.message;

			if (data) {
				frappe.model.set_value(cdt, cdn, "account_currency", data.account_currency);
			}
		});
	},
	"allocated_amount": (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);
		
		let base_allocated_amount = flt(row.allocated_amount) * flt(row.against_exchange_rate);
		frappe.model.set_value(cdt, cdn, "base_allocated_amount", base_allocated_amount);
	},
	"party_exchange_rate": (frm, cdt, cdn) => {
		
		let row = frappe.get_doc(cdt, cdn);

		if (flt(row.party_exchange_rate) <= flt(0.00)) {
			frappe.model.set_value(cdt, cdn, "party_exchange_rate", 1.000);
			frappe.throw(__("Exchange Rate is invalid"));
		}

		let base_total_amount = flt(row.total_amount) * flt(row.party_exchange_rate);
		let base_outstanding_amount = flt(row.outstanding_amount) * flt(row.party_exchange_rate);

		frappe.model.set_value(cdt, cdn, "base_total_amount", base_total_amount);
		frappe.model.set_value(cdt, cdn, "base_outstanding_amount", base_outstanding_amount);
	},
	"against_exchange_rate": (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);

		if (flt(row.against_exchange_rate) <= flt(0.00)) {
			frappe.model.set_value(cdt, cdn, "against_exchange_rate", 1.000);
			frappe.throw(__("Exchange Rate is invalid"));
		}

		let base_allocated_amount = flt(row.allocated_amount) * flt(row.against_exchange_rate);
		frappe.model.set_value(cdt, cdn, "base_allocated_amount", base_allocated_amount);

	},
	"allocated_amount": (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);

		let base_allocated_amount = row.allocated_amount * row.against_exchange_rate;

		if (flt(row.allocated_amount) < flt(0.00)) {
			frappe.model.set_value(cdt, cdn, "allocated_amount", row.outstanding_amount);
			frappe.throw(__("Allocated Amount cannot be less than zero!"));
		}

		frappe.model.set_value(cdt, cdn, "base_allocated_amount", base_allocated_amount);
	},
	"base_allocated_amount": (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);

		let base_allocated_amount_precisioned = flt(row.base_allocated_amount, precision("base_allocated_amount", row));
		let base_outstanding_amount_precisioned = flt(row.base_outstanding_amount, precision("base_outstanding_amount", row));

		if (base_allocated_amount_precisioned > base_outstanding_amount_precisioned) {

			let allocated_amount = row.base_outstanding_amount / row.against_exchange_rate;

			frappe.model.set_value(cdt, cdn, "allocated_amount", allocated_amount);
			frappe.throw(__("Allocated Amount cannot be greater than outstanding amount!"));
		}

		frm.trigger("calculate_totals");
	},
});