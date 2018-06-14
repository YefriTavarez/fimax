// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Income Receipt Items', {
	"before_income_receipt_items_remove": (frm, cdt, cdn) => {
		let doc = frappe.get_doc(cdt, cdn);

		if (frm.doc.posting_date > doc.repayment_date || doc.status == "Overdue") {
			frappe.throw(__("Cannot remove Loan Charge as it is already due!"));
		}
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