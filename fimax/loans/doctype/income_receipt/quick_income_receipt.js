// Copyright (c) 2018, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("fimax.quick_entry");

$.extend(fimax.quick_entry, {
	"get_total_amount": (frm) => {
		const insurance_amount = cur_prompt.get_value("insurance_amount"),
			gps_amount = cur_prompt.get_value("gps_amount"),
			capital_amount = cur_prompt.get_value("capital_amount"),
			interest_amount = cur_prompt.get_value("interest_amount"),
			repayment_amount = cur_prompt.get_value("repayment_amount"),
			recovery_amount = cur_prompt.get_value("recovery_amount"),
			fine_amount = cur_prompt.get_value("fine_amount");
		
		const total_amount = flt(insurance_amount) + flt(gps_amount) + flt(capital_amount) 
			+ flt(interest_amount) + flt(repayment_amount) + flt(recovery_amount) + flt(fine_amount);

		cur_prompt.set_value("total_amount", total_amount || "0.000");
	},
	"get_fields": (frm) => {
		return [
			{
				"fieldtype": "Section Break",
				"label": __("Repayment"),
			},
			{
				"fieldtype": "Currency",
				"fieldname": "capital_amount",
				"label": __("Capital Amount"),
				"default": "0.000",
				"precision": 2,
				"reqd": true,
				"hidden": !frappe.boot.conf.detail_repayment_amount,
				"onchange": event => fimax.quick_entry.capital_amount(frm, event)
			},
			{
				"fieldtype": "Currency",
				"fieldname": "interest_amount",
				"label": __("Interest Amount"),
				"default": "0.000",
				"precision": 2,
				"reqd": true,
				"hidden": !frappe.boot.conf.detail_repayment_amount,
				"onchange": event => fimax.quick_entry.interest_amount(frm, event)
			},
			{
				"fieldtype": "Currency",
				"fieldname": "repayment_amount",
				"label": __("Repayment Amount"),
				"default": "0.000",
				"precision": 2,
				"reqd": true,
				"hidden": frappe.boot.conf.detail_repayment_amount,
				"onchange": event => fimax.quick_entry.repayment_amount(frm, event)
			},
			{
				"fieldtype": "Section Break",
				"label": __("Other Charges"),
			},
			{
				"fieldtype": "Currency",
				"fieldname": "insurance_amount",
				"label": __("Insurance Amount"),
				"default": "0.000",
				"precision": 2,
				"reqd": true,
				"hidden": !frappe.loan_charges_count["Insurance"],
				"onchange": event => fimax.quick_entry.insurance_amount(frm, event)
			},
			{
				"fieldtype": "Currency",
				"fieldname": "gps_amount",
				"label": __("GPS Amount"),
				"default": "0.000",
				"precision": 2,
				"reqd": true,
				"hidden": !frappe.loan_charges_count["GPS"],
				"onchange": event => fimax.quick_entry.gps_amount(frm, event)
			},
			{
				"fieldtype": "Currency",
				"fieldname": "fine_amount",
				"label": __("Fine Amount"),
				"default": "0.000",
				"precision": 2,
				"hidden": !frappe.loan_charges_count["Late Payment Fee"],
				"reqd": true,
				"onchange": event => fimax.quick_entry.fine_amount(frm, event)
			},
			{
				"fieldtype": "Currency",
				"fieldname": "recovery_amount",
				"label": __("Recovery Amount"),
				"default": "0.000",
				"precision": 2,
				"hidden": !frappe.loan_charges_count["Recovery Expenses"],
				"reqd": true,
				"onchange": event => fimax.quick_entry.recovery_amount(frm, event)
			},
			{
				"fieldtype": "Section Break"
			},
			{
				"fieldtype": "Currency",
				"fieldname": "total_amount",
				"label": __("Total Amount"),
				"description": __("Total Allocated Amount"),
				"default": "0.000",
				"precision": 2,
				"reqd": frappe.boot.conf.enable_total_amount_in_quick_entry,
				"read_only": !frappe.boot.conf.enable_total_amount_in_quick_entry,
				"onchange": event => fimax.quick_entry.total_amount(frm, event)
			},
		];
	},
	"insurance_amount": (frm, event) => {
		// const value = target.value;

		fimax.quick_entry.get_total_amount(frm);
	},
	"gps_amount": (frm, event) => {
		// const value = target.value;
		
		fimax.quick_entry.get_total_amount(frm);
	},
	"fine_amount": (frm, event) => {
		// const value = target.value;
		
		fimax.quick_entry.get_total_amount(frm);
	},
	"capital_amount": (frm, event) => {
		// const value = target.value;
		
		fimax.quick_entry.get_total_amount(frm);
	},
	"interest_amount": (frm, event) => {
		// const value = target.value;
		
		fimax.quick_entry.get_total_amount(frm);
	},
	"recovery_amount": (frm, event) => {
		// const value = target.value;
		
		fimax.quick_entry.get_total_amount(frm);
	},
	"repayment_amount": (frm, event) => {
		// const value = target.value;
		
		fimax.quick_entry.get_total_amount(frm);
	},
	"total_amount": (frm, event) => {
		// const value = target.value;

		// this.get_total_amount(frm);
	},
});
