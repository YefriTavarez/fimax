import frappe

def create_simple_role(role):
	return frappe.get_doc({
		"desk_access": 1,
		"disabled": 0,
		"doctype": "Role",
		"role_name": role,
		"two_factor_auth": 0
	})