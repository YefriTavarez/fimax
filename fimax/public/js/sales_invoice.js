// Copyright (c) 2022, Yefri Tavarez and contributors
// For license information, please see license.txt

/* eslint-disable */

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		frm.trigger("add_custom_buttons");
	},
	add_custom_buttons(frm) {
		frappe.run_serially([
			() => frm.trigger("setup_onload_data"),
			() => frm.trigger("add_create_loan_button"),
		]);
	},
	setup_onload_data(frm) {
		const { doc } = frm;
		const { __onload: onload } = doc;

		doc.loan = null;

		if (!onload) {
			return "No onload data found";
		}

		if (onload.loan) {
			doc.loan = onload.loan;
		}
	},
	add_create_loan_button(frm) {
		const { doc } = frm;

		if (doc.docstatus !== 1) {
			return "Only for submitted documents";
		}

		if (doc.is_return) {
			return "Not for returns";
		}

		if (doc.outstanding_amount <= 0) {
			return "Not for paid invoices";
		}

		if (doc.loan) {
			return "Already has a loan";
		}

		const label = __("Loan");
		const action = () => frm.trigger("create_loan");
		const parent = __("Create");

		frm.add_custom_button(label, action, parent);
	},
	create_loan(frm) {
		const { doc } = frm;

		frappe.call({
			method: "fimax.loans.doctype.loan_application.loan_application.create_from_sales_invoice",
			args: {
				sales_invoice: doc.name,
			},
			callback: ({ message: loan_application }) => {
				const docs = frappe.model.sync(loan_application);

				if (docs && docs[0]) {
					frappe.set_route("Form", "Loan Application", docs[0].name);
				}
			},
		});
	},
});
