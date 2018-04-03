// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan");
frappe.ui.form.on('Loan', {
	"setup": (frm) => {
		let event_list = ["set_queries"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"refresh": (frm) => {
		let event_list = ["set_status_indicators", "add_custom_buttons"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"onload": (frm) => {
		let event_list = ["toggle_mandatory_fields"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"set_queries": (frm) => {
		let event_list = ["set_loan_application_query", "set_party_account_query"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"add_custom_buttons": (frm) => {
		if (frm.is_new()) {
			let button_list = ["add_new_vehicule_button",
				"add_new_property_button"];
			$.map(button_list, (event) => frm.trigger(event));

			frm.page.set_inner_btn_group_as_primary(__("New"));
		}
	},
	"set_status_indicators": (frm) => {
		let grid = frm.get_field('loan_schedule').grid;

		grid.wrapper.find("div.rows .grid-row").each((idx, vhtml) => {
			let doc = frm.doc.loan_schedule[idx];

			let html = $(vhtml);

			let indicator = {
				"Pending": "indicator orange",
				"Overdue": "indicator red",
				"Partially Paid": "indicator yellow",
				"Paid": "indicator green",
			}[doc.status];

			// let's remove any previous set class
			$.map(["orange", "red", "yellow", "green"], (color) => {
				html.find("div[data-fieldname=status] .static-area.ellipsis")
					.removeClass(__("indicator {0}", [color]));
			});

			html.find("div[data-fieldname=status] .static-area.ellipsis").addClass(indicator);
		});
	},
	"set_loan_application_query": (frm) => {
		frm.set_query("loan_application", () => {
			return {
				"filters": {
					"docstatus": 1
				}
			};
		});
	},
	"set_party_account_query": (frm) => {
		frm.set_query("party_account", () => {
			return {
				"filters": {
					"is_group": 0,
					"account_currency": frm.doc.currency,
					"account_type": "Receivable"
				}
			};
		});
	},
	"toggle_mandatory_fields": (frm) => {
		let event_list = ["toggle_loan_type_mandatory_fields"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"toggle_loan_type_mandatory_fields": (frm) => {
		if (!frm.doc.loan_type) {
			return 0;
		}

		frappe.db.get_value(frm.fields_dict.loan_type.df.options, frm.doc.loan_type, "asset_type")
			.done((response) => {
				let data = response.message;
				asset_type = data && data["asset_type"];

				if (asset_type) {
					frm.toggle_reqd("asset", true);
					frm.toggle_reqd("asset_type", true);
					frm.toggle_enable("asset", true);
					frm.toggle_enable("asset_type", true);

					frm.doc.asset_type = asset_type;
					frm.doc.asset = undefined;
				} else {
					frm.toggle_reqd("asset", false);
					frm.toggle_reqd("asset_type", false);
					frm.toggle_enable("asset", false);
					frm.toggle_enable("asset_type", false);

					frm.doc.asset_type = undefined;
					frm.doc.asset = undefined;
				}
				
				frm.refresh_fields();
					
			}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party default currency!")));
	},
	"loan_application": (frm) => {
		if (frm.doc.loan_application) {
			frm.call("make_loan").done((response) => {
				let doc = response.message;

				if (doc) {
					frappe.model.sync(doc) && fimax.utils.view_doc(doc);
				}
			}); 
		}
	},
	"add_new_vehicule_button": (frm) => {
		frm.add_custom_button(__("Vehicle"), () => frm.trigger("new_vehicule"), __("New"));
	},
	"add_new_property_button": (frm) => {
		frm.add_custom_button(__("Property"), () => frm.trigger("new_property"), __("New"));
	},
	"new_vehicule": (frm) => {
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("asset_type", "Car"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Car")
		]);
	},
	"new_property": (frm) => {
		frappe.run_serially([
			() => frm.trigger("remember_current_route"),
			() => frm.set_value("asset_type", "Property"),
			() => frappe.timeout(0.5),
			() => frappe.new_doc("Property")
		]);
	},
	"remember_current_route": (frm) => {
		fimax.loan.url = frappe.get_route();
	},
	"loan_type": (frm) => {
		if (frm.doc.loan_type) {
			frappe.run_serially([
				() => frappe.timeout(1.5),
				() => frm.trigger("toggle_loan_type_mandatory_fields")
			]);
		}
	},
	"mode_of_payment": (frm) => {
		frappe.db.get_value("Mode of Payment Account", {
			"parent": frm.doc.mode_of_payment,
			"company": frm.doc.company
		}, ["default_account"]).then((response) => {
			let data = response.message;

			if (! (data && data["default_account"])) {
				frappe.msgprint(repl(`Please set default Cash or Bank account in Mode of Payment 
					<a href="/desk#Form/Mode of Payment/%(mode_of_payment)s">%(mode_of_payment)s</a>
					for company %(company)s`, frm.doc));

				frm.set_value("mode_of_payment", undefined);
			}
		});
	},
});
