import frappe

def get_boot_info(boot_info):
	boot_info.conf = frappe.get_single("Control Panel")

	dark_theme = frappe.get_value("User", frappe.session.user, "dark_theme")
	boot_info.user.defaults.dark_theme = dark_theme

