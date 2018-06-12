// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company', {
	"onload": (frm) => {
		let events = ["set_interest_income_account_query", "setup_tax_id_mask"];

		$.map(events, event => frm.trigger(event));
	},
	"set_interest_income_account_query": (frm) => {
		frm.set_query("default_interest_income_account", () => {
			return {
				"filters": {
					"account_type": "Income Account"
				}
			};
		});
	},
	"setup_tax_id_mask": (frm) => {
		$("input[data-fieldname=tax_id]").mask("000-00000-0");
	},
});
