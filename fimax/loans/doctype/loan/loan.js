// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan', {
	"refresh": (frm) => {
		let event_list = ["set_status_indicators"];

		$.map(event_list, (event) => frm.trigger(event));
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
	}
});
