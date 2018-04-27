// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company', {
	"onload": (frm) => {
		frm.set_query("default_interest_income_account", () => {
			return {
				"filters": {
					"account_type": "Income Account"
				}
			};
		});
	}
});
