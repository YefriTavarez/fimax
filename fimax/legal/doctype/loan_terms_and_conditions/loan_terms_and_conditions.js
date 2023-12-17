// Copyright (c) 2018, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Terms and Conditions', {
	"refresh": function(frm) {
		if (frm.doc.docstatus != 0 || frm.is_new()) { return ; }

		if (frm.events.validate_both(frm)) {
			$.map(["add_custom_buttons"], event => frm.trigger(event));
		}
	},
	"add_custom_buttons": function(frm) {
		frm.add_custom_button(__("Sync With Template"), function() {
			frm.trigger("update_terms_and_conditions");
		});
	},
	"update_terms_and_conditions": function(frm) {
		if (frm.events.validate_both(frm)) {
			frm.trigger("fetch_terms_and_conditions");
		}
	},
	"fetch_terms_and_conditions": function(frm) {
		frm.call("get_terms_and_conditions")
			.then(response => {
				frappe.run_serially([
					() => frm.refresh(),
					() => frm.dirty()
				]);
			});
	},
	"validate_both": function({ doc }) {
		if (doc.loan && doc.terms_template) {
			return true;
		}

		return false;
	},
	"loan": function(frm) {
		frm.trigger("update_terms_and_conditions");
	},
	"terms_template": function(frm) {
		frm.trigger("update_terms_and_conditions");
	},
});
