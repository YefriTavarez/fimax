// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Income Receipt', {
	"setup": (frm) => {
		frm.trigger("set_queries");
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
		frm.set_query("account", "income_receipt_items", {
			"account_type": "Receivable",
			"company": frm.doc.company
		});
	},
	"set_against_account_query": (frm) => {
		frm.set_query("against_account", "income_receipt_items", {
			"account_type": ["in", "Bank, Cash"],
			"company": frm.doc.company
		});
	},
	"set_income_account_query": (frm) => {
		frm.set_query("income_account", {
			"account_type": ["in", "Bank, Cash"],
			"company": frm.doc.company
		});
	},
	"set_dynamic_labels": (frm) => {
		$.map(frm.meta.fields, field => {
			if (field.fieldtype == "Currency") {
				let new_label = __("{0} ({1})", [field.label, frm.doc.currency||""]);
				frm.set_df_property(field.fieldname, "label", new_label);
			}
		});
	},
	"loan": (frm) => {
		if (frm.doc.loan) {
			frm.trigger("set_missing_values");
		} else {
			frm.trigger("clear_all_fields");
		}

		frm.trigger("set_dynamic_labels");
	},
	"posting_date": (frm) => {
		frm.trigger("fetch_loan_charges");
	},
	"clear_all_fields": (frm) => {
		$.map(frm.meta.fields, (field) => { 
			if (!["Section Break", "Column Break"].includes(field.fieldtype)) { 
				frm.set_value(field.fieldname, undefined); 
			}
		});
	},
	"set_missing_values": (frm) => {
		$.map(["fetch_party", "fillup_loan_dependant_fields", 
			"fetch_loan_charges"], (event) => frm.trigger(event));
	},
	"fetch_party": (frm) => {
		let doctype = "Loan";
		let docname = frm.doc.loan;

		if (docname) {
			frappe.provide(__("locals.{0}.{1}", [doctype, docname]));

			frappe.db.get_value(doctype, docname, "*")
				.done((response) => {

					let doc = response.message;

					if (doc) {
						locals[doctype][docname] = doc;
					}
				}).then(() => frm.trigger("fillup_loan_dependant_fields"));
		}
	},
	"fillup_loan_dependant_fields": (frm) => {
		let field_list = ["company", "mode_of_payment", 
			"party_type", "party", "party_name", "currency"];

		$.map(field_list, field => frm.set_value(field, 
			locals["Loan"][frm.doc.loan][field]));
	},
	"fetch_loan_charges": (frm) => {
		frm.call("grab_loan_charges").done(() => frm.trigger("set_dynamic_labels"));
	},
	"mode_of_payment": (frm) => {
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
			}
		});
	},
	"income_account": (frm) => {
		$.map(frm.doc.income_receipt_items, (row) => {
			frappe.model.set_value(row.doctype, row.docname, "against_account", frm.doc.income_account);
		});
	},
	"exchange_rate": (frm) => {
		$.map(frm.doc.income_receipt_items, (row) => {
			frappe.model.set_value(row.doctype, row.docname, "exchange_rate", frm.doc.exchange_rate);
		});
	},
	"calculate_totals": (frm, cdt, cdn) => {
		let total_paid = 0.000;
		let grand_total = 0.000;
		let total_outstanding = 0.000;

		$.map(frm.doc.income_receipt_items, (row) => {
			total_paid += flt(row.allocated_amount);
			grand_total += flt(row.total_amount);
			total_outstanding += flt(row.outstanding_amount);
		});

		frm.set_value("total_paid", total_paid); 
		frm.set_value("grand_total", grand_total); 
		frm.set_value("total_outstanding", total_outstanding); 
	},
});

frappe.ui.form.on('Income Receipt Items', {
	"add_income_receipt_items": (frm, cdt, cdn) => {
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
	"allocated_amount_in_account_currency": (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);

		if (flt(row.allocated_amount_in_account_currency) < flt(0.00)) {
			frappe.model.set_value(cdt, cdn, "allocated_amount_in_account_currency", row.outstanding_amount);
			frappe.throw(__("Allocated Amount cannot be less than zero!"));
		}
		
		let allocated_amount = flt(row.allocated_amount_in_account_currency) * flt(row.exchange_rate);
		frappe.model.set_value(cdt, cdn, "allocated_amount", allocated_amount);
	},
	"exchange_rate": (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);

		if (!flt(row.exchange_rate) || flt(row.exchange_rate) < flt(0.00)) {
			frappe.model.set_value(cdt, cdn, "exchange_rate", 1.000);
			frappe.throw(__("Exchange Rate is invalid"));
		}

		let allocated_amount = flt(row.allocated_amount_in_account_currency) * flt(row.exchange_rate);
		frappe.model.set_value(cdt, cdn, "allocated_amount", allocated_amount);
	},
	"allocated_amount": (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);

		if (flt(row.allocated_amount) > flt(row.outstanding_amount)) {
			frappe.model.set_value(cdt, cdn, "allocated_amount", row.outstanding_amount);
			frappe.throw(__("Allocated Amount cannot be greater than outstanding amount!"));
		}

		let difference_amount = flt(row.outstanding_amount) - flt(row.allocated_amount);

		if (flt(difference_amount) < flt(0.000)) {
			frappe.throw(__("Somehow difference amount amount is less than zero!"));
		}

		frm.set_value("difference_amount", difference_amount);

		frm.trigger("calculate_totals");
	},
});