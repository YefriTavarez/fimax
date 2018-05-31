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
		let event_list = [
			"toggle_mandatory_fields", 
			"work_on_exchange_rate", 
			"work_on_dynamic_labels", 
		];

		$.map(event_list, (event) => frm.trigger(event));
	},
	"validate": (frm) => {
		let event_list = [
			"validate_exchange_rate", 
		];

		$.map(event_list, (event) => frm.trigger(event));
	},
	"validate_exchange_rate": (frm) => {
		if (frm.doc.currency != frm.doc.company_currency && frm.doc.exchange_rate == 1.000) {
			frappe.msgprint(__("Different currencies have been detected and exchange rate of 1"));
		}
	},
	"set_queries": (frm) => {
		let event_list = [
			"set_loan_application_query", 
			"set_party_account_query",
			"set_income_account_query", 
			"set_disbursement_account_query", 
		];

		$.map(event_list, (event) => frm.trigger(event));
	},
	"add_custom_buttons": (frm) => {
		if (frm.is_new()) {
			let button_list = ["add_new_vehicle_button",
				"add_new_property_button"];
			$.map(button_list, (event) => frm.trigger(event));

			frm.page.set_inner_btn_group_as_primary(__("New"));
		} else {
			// if () {} unfinished
		}
		else{
			let button_list = ["add_new_insurance_card_button", 
				"add_view_income_recepit_button"];
			$.map(button_list, (event) => frm.trigger(event));
			
			frm.page.set_inner_btn_group_as_primary(__("Make"));
		}
		else{
			let button_list = ["add_new_insurance_card_button", 
				"add_view_income_recepit_button"];
			$.map(button_list, (event) => frm.trigger(event));
			
			frm.page.set_inner_btn_group_as_primary(__("Make"));
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
				"query": "fimax.queries.loan_unlinked_application_query",
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
	"set_income_account_query": (frm) => {
		frm.set_query("income_account", () => {
			return {
				"filters": {
					"is_group": 0,
					"account_currency": frm.doc.currency,
					"account_type": "Income Account"
				}
			};
		});
	},
	"set_disbursement_account_query": (frm) => {
		frm.set_query("disbursement_account", () => {
			return {
				"filters": {
					"is_group": 0,
					"account_currency": frm.doc.currency,
					"account_type": ["in", "Bank, Cash"]
				}
			};
		});
	},
	"set_dynamic_labels": (frm) => {
		$.map(frm.meta.fields, field => {
			if (field.fieldtype == "Currency") {
				let new_label = __("{0} ({1})", [field.label, frm.doc.currency]);
				frm.set_df_property(field.fieldname, "label", new_label);
			}
		});
	},
	"toggle_mandatory_fields": (frm) => {
		let event_list = ["toggle_loan_type_mandatory_fields"];
		$.map(event_list, (event) => frm.trigger(event));
	},
	"toggle_loan_type_mandatory_fields": (frm) => {
		if (!frm.doc.loan_type) { return 0; }

		frappe.db.get_value(frm.fields_dict.loan_type.df.options, frm.doc.loan_type, "asset_type")
			.done((response) => {
				let data = response.message;
				let asset_type = data && data["asset_type"];

				$.map(["toggle_reqd", "toggle_enable"], (func) => {
					frm[func](["asset_type", "asset"], !! asset_type);
				});
				
				if (asset_type) {
					frm.doc.asset_type = asset_type;
				} else {
					frm.doc.asset_type = frm.doc.asset = undefined;
				}
				
				frm.refresh_fields();
					
			}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party default currency!")));
	},
	"currency": (frm) => {
		frm.trigger("work_on_exchange_rate");
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
	"repayment_day_of_the_month": (frm) => {
		frm.call("update_repayment_schedule_dates")
			.done(() => frm.refresh()); // to remove as this is optional now
	},
	"asset_type": (frm) => {
		frm.set_value("asset", undefined);
	},
	"add_new_vehicle_button": (frm) => {
		frm.add_custom_button(__("Vehicle"), () => frm.trigger("new_vehicle"), __("New"));
	},
	"add_new_insurance_card_button": (frm) => {
		frm.add_custom_button(__("Insurance"), () => frm.trigger("make_insurance_card"), __("Make"));
	},
	"add_new_property_button": (frm) => {
		frm.add_custom_button(__("Property"), () => frm.trigger("new_property"), __("New"));
	},
	"add_view_income_recepit_button": (frm) => {
		frm.add_custom_button(__("Income Receipts"), () => frm.trigger("view_income_receipts"), __("View"));
	},
	"new_vehicle": (frm) => {
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
	"make_insurance_card": (frm) => {
		let opts = {
			"method": "fimax.api.create_insurance_card_from_loan"
		};

		opts.args = {
			"doc": frm.doc
		}

		frappe.call(opts).done((response) => {
			let doc = response.message;

			doc = frappe.model.sync(doc)[0];
			frappe.set_route("Form", doc.doctype, doc.name);
		}).fail((exec) => frappe.msgprint(__("There was an error while creating the Insurance Card")));
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
	"work_on_exchange_rate": (frm) => {
		if (frm.doc.currency == frm.doc.company_currency) {
			frm.set_value("exchange_rate", 1);
			frm.toggle_enable("exchange_rate", false);
		} else {
			frm.toggle_enable("exchange_rate", true);
		}
	},
	"work_on_dynamic_labels": (frm) => {
		frm.trigger("set_dynamic_labels");
	},
});
