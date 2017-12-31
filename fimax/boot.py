import frappe

def get_boot_info(boot_info):
	boot_info.conf = frappe.get_single("Control Panel")