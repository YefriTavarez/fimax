frappe.ui.form.on("User", {
	"refresh": (frm) => {
		if(frm.doc.name == frappe.session.user && !frm.doc.__unsaved
			&& (frm.doc.dark_theme || frappe.boot.user.defaults.dark_theme)
			&& frm.doc.dark_theme !== frappe.boot.user.defaults.dark_theme) {
			frappe.msgprint(__("Refreshing..."));
			window.location.reload(true);
		}
	}
})