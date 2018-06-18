frappe.ui.form.on("Loan Repayment Schedule", {
	"view_vouchers": (frm, cdt, cdn) => {
		// let row = frappe.get_doc(cdt, cdn);

		frappe.set_route("List", "Loan Charges", {
			"reference_type": cdt,
			"reference_name": cdn
		});
	}
});