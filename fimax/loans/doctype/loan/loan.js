// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.loan");
frappe.ui.form.on('Loan', {
	"setup": (frm) => {
		let event_list = ["set_queries"];
		jQuery.map(event_list, (event) => frm.trigger(event));
	},
	"refresh": (frm) => {
		let event_list = ["set_status_indicators", "add_custom_buttons"];
		jQuery.map(event_list, (event) => frm.trigger(event));

		if (frm.is_new()) {
			frm.trigger("set_defaults");
		}
	},
	"onload": (frm) => {
		let event_list = [
			"toggle_mandatory_fields",
			"work_on_exchange_rate",
			"work_on_dynamic_labels",
		];

		jQuery.map(event_list, (event) => frm.trigger(event));
	},
	"onload_post_render": (frm) => {
		frappe.realtime.on("real_progress", function (data) {
			frappe.show_progress(__("Wait"), flt(data.progress));

			if (cstr(data.progress) == "100") {
				frappe.run_serially([
					() => frappe.timeout(1),
					() => frappe.hide_progress()
				]);
			}
		});
	},
	"validate": (frm) => {
		let event_list = [
			"validate_exchange_rate",
		];

		jQuery.map(event_list, (event) => frm.trigger(event));
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

		jQuery.map(event_list, (event) => frm.trigger(event));
	},
	"add_custom_buttons": (frm) => {
		const { doc, page } = frm;

		if (frm.is_new()) {
			let button_list = ["add_new_vehicle_button",
				"add_new_property_button"];
			jQuery.map(button_list, (event) => frm.trigger(event));

			frm.page.set_inner_btn_group_as_primary(__("New"));
		} else {
			let button_list = ["add_new_insurance_card_button",
				"add_new_gps_installation_button", "add_view_income_recepit_button"];
			jQuery.map(button_list, (event) => frm.trigger(event));

			frm.page.set_inner_btn_group_as_primary(__("Hacer"));
		}


		if (doc.docstatus === 1) {
			frm.trigger("add_relocate_repayments_btn");

			if (frappe.boot.user.can_cancel.includes("Sales Invoice")) {
				page.set_secondary_action(
					__("Cancel"),
					_ => {
						frm.call("cancel_loan")
							.then(() => {
								frm.reload_doc();
							});
					}
				)
			}
		}
	},
	"set_defaults": (frm) => {
		const { doc } = frm;
		const doctype = "Company Defaults",
			filters = doc.company,
			fieldname = ["default_mode_of_payment", "disbursement_account"],
			callback = ({ default_mode_of_payment, disbursement_account }) => {
				jQuery.each({
					"mode_of_payment": default_mode_of_payment,
					"disbursement_account": disbursement_account
				}, (key, value) => frm.set_value(key, value || ""));
			};

		frappe.db.get_value(doctype, filters, fieldname, callback);

		if (frm.is_new()) {
			doc.status = "Open";
		}
	},
	"set_status_indicators": (frm) => {
		const { doc } = frm;

		let grid = frm.get_field('loan_schedule').grid;

		grid.wrapper.find("div.rows .grid-row").each((idx, vhtml) => {
			const childoc = doc.loan_schedule[idx];

			const html = jQuery(vhtml);

			const indicator = {
				"Pending": "indicator orange",
				"Overdue": "indicator red",
				"Partially": "indicator yellow",
				"Paid": "indicator green",
			}[childoc.status];

			// let's remove any previous set class
			jQuery.map(["orange", "red", "yellow", "green"], (color) => {
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
		let currency_fields = jQuery.grep(frm.meta.fields, field => {
			if (field.fieldtype == "Currency") {
				return true;
			}

			return false;
		}).map(field => field.fieldname);

		frm.set_currency_labels(currency_fields, frm.doc.currency);
	},
	"toggle_mandatory_fields": (frm) => {
		let event_list = ["toggle_loan_type_mandatory_fields"];
		jQuery.map(event_list, (event) => frm.trigger(event));
	},
	"toggle_loan_type_mandatory_fields": (frm) => {
		if (!frm.doc.loan_type) { return 0; }

		frappe.db.get_value(frm.fields_dict.loan_type.df.options, frm.doc.loan_type, "asset_type")
			.done((response) => {
				let data = response.message;
				let asset_type = data && data["asset_type"];

				jQuery.map(["toggle_reqd", "toggle_enable"], (func) => {
					frm[func](["asset_type", "asset"], !!asset_type);
				});

				if (asset_type) {
					frm.doc.asset_type = asset_type;
				} else {
					frm.doc.asset_type = frm.doc.asset = undefined;
				}

				frm.refresh_fields();

			}).fail((exec) => frappe.msgprint(__("There was a problem while loading the party default currency!")));
	},
	"party": (frm) => {
		if (frm.doc.party) {
			frm.call("set_accounts")
				.then(response => frm.refresh());
		}
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
	"add_new_gps_installation_button": (frm) => {
		frm.add_custom_button(__("GPS Installation"), () => frm.trigger("make_gps_installation"), __("Hacer"));
	},
	"add_new_insurance_card_button": (frm) => {
		frm.add_custom_button(__("Insurance Card"), () => frm.trigger("make_insurance_card"), __("Hacer"));
	},
	"add_new_property_button": (frm) => {
		frm.add_custom_button(__("Property"), () => frm.trigger("new_property"), __("New"));
	},
	"add_view_income_recepit_button": (frm) => {
		frm.add_custom_button(__("Income Receipts"), () => frm.trigger("view_income_receipts"), __("View"));
	},
	"add_sync_with_loan_charges_button": (frm) => {
		frm.add_custom_button(__("Sync With Loan Charges"), () => frm.trigger("sync_with_loan_charges"));
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
		};

		frappe.call(opts).done((response) => {
			let doc = response.message;
			if (doc) {
				frappe.model.sync(doc);
				fimax.utils.view_doc(doc);
			}
		}).fail((exec) => frappe.msgprint(__("There was an error while creating the Insurance Card")));
	},
	"make_gps_installation": (frm) => {
		let opts = {
			"method": "fimax.api.create_gps_installation_from_loan"
		};

		opts.args = {
			"doc": frm.doc
		};

		frappe.call(opts).done((response) => {
			let doc = response.message;
			if (doc) {
				frappe.model.sync(doc);
				fimax.utils.view_doc(doc);
			}
		}).fail((exec) => frappe.msgprint(__("There was an error while creating the GPS Installation")));
	},
	"view_income_receipts": (frm) => {
		frappe.set_route("List", "Income Receipt", {
			"loan": frm.docname
		});
	},
	"sync_with_loan_charges": (frm) => {
		
		frm.call("sync_this_with_loan_charges")
			.then(() => frm.reload_doc());
			
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
		const { doc } = frm;

		if (!doc.mode_of_payment) {
			return "Ignore if no mode of payment";
		}

		frappe.db.get_value("Mode of Payment Account", {
			"parent": doc.mode_of_payment,
			"company": doc.company
		}, ["default_account"], (response) => {
			let data = response.message;
			const message_str = `
				Please set default Cash or Bank account in Mode of Payment 
				<a
					target="_blank"
					href="/app/mode-of-payment/%(mode_of_payment)s"
				>
					%(mode_of_payment)s
				</a> for company %(company)s
			`;

			if (data && !data.default_account) {
				frappe.msgprint(
					repl(
						message_str, doc
					)
				);

				frm.set_value("mode_of_payment", undefined);
			}
		}, "Mode of Payment");
	},
	"work_on_exchange_rate": (frm) => {
		const { doc } = frm;

		if (doc.currency == doc.company_currency) {
			frm.set_value("exchange_rate", 1);
			frm.toggle_enable("exchange_rate", false);
		} else {
			frm.toggle_enable("exchange_rate", true);
		}
	},
	"work_on_dynamic_labels": (frm) => {
		frm.trigger("set_dynamic_labels");
	},

	"add_relocate_repayments_btn": (frm) => {
		const label = __('Relocate Repayment');
		const action = () => frm.trigger("handle_relocate_repayments");

		frm.add_custom_button(label, action);
	},
	handle_relocate_repayments(frm) {
		const { doc } = frm;
		const options = doc.loan_schedule
			.filter(row => row.status === "Partially" || row.status === "Pending")
			.map(row => row.idx)
			;
		

		const fields = [
			{
				fieldtype: 'Select',
				fieldname: 'repayment_period',
				label: 'Repayment Period',
				reqd: 1,
				options: options,
			},
			{
				fieldtype: 'Date',
				fieldname: 'date',
				reqd: 1,
				label: 'Date',
			},
		];

		// if (!options.length) {
		// 	frappe.throw(
		// 		__("There must be at least one repayment full paid to proceed")
		// 	);
		// }

		const callback = ({ repayment_period: idx, date: starting_date }) => {
			const method = "relocate_repayment";
			frm.call(method, { idx, starting_date });
		};

		const title = __("Select the relocation date");
		const primary_label = __("Relocate");

		frappe.prompt(fields, callback, title, primary_label);
	},
});

{% include "fimax/loans/doctype/loan_repayment_schedule/loan_repayment_schedule.js" %}
