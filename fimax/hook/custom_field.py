import frappe

def add_reqd_custom_fields_in_company():
	if frappe.db.exists("Custom Field", 
		"Company-default_interest_income_account"):
		return
		
	custom_field = frappe.get_doc({
		'allow_on_submit': 0,
		'bold': 0,
		'collapsible': 0,
		'collapsible_depends_on': None,
		'columns': 0,
		'default': None,
		'depends_on': None,
		'description': None,
		'docstatus': 0,
		'doctype': 'Custom Field',
		'dt': 'Company',
		'fieldname': 'default_interest_income_account',
		'fieldtype': 'Link',
		'hidden': 0,
		'ignore_user_permissions': 0,
		'ignore_xss_filter': 0,
		'in_global_search': 0,
		'in_list_view': 0,
		'in_standard_filter': 0,
		'insert_after': 'default_income_account',
		'label': 'Default Interest Income Account',
		'no_copy': 0,
		'options': 'Account',
		'permlevel': 0,
		'precision': '',
		'print_hide': 0,
		'print_hide_if_no_value': 0,
		'print_width': None,
		'read_only': 0,
		'report_hide': 0,
		'reqd': 0,
		'search_index': 0,
		'unique': 0,
		'width': None
	}).save(ignore_permissions=True)

def add_reqd_custom_fields_in_user():
	if frappe.db.exists("Custom Field", "User-dark_theme"): return
		
	custom_field = frappe.get_doc({
		'allow_on_submit': 0,
		'bold': 0,
		'collapsible': 0,
		'collapsible_depends_on': None,
		'columns': 0,
		'default': '1',
		'depends_on': None,
		'description': None,
		'docstatus': 0,
		'doctype': 'Custom Field',
		'dt': 'User',
		'fieldname': 'dark_theme',
		'fieldtype': 'Check',
		'hidden': 0,
		'ignore_user_permissions': 0,
		'ignore_xss_filter': 0,
		'in_global_search': 0,
		'in_list_view': 0,
		'in_standard_filter': 0,
		'insert_after': 'user_image',
		'label': 'Use Dark Theme',
		'no_copy': 0,
		'options': None,
		'permlevel': 0,
		'precision': '',
		'print_hide': 0,
		'print_hide_if_no_value': 0,
		'print_width': None,
		'read_only': 0,
		'report_hide': 0,
		'reqd': 0,
		'search_index': 0,
		'unique': 0,
		'width': None
	}).save(ignore_permissions=True)
