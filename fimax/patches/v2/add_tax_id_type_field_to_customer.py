import frappe

def execute():
	if frappe.db.exists("Custom Field", {
		"name": "Customer-tax_id_type"
	}): return

	frappe.get_doc({
		'allow_on_submit': 0,
		'collapsible': 0,
		'collapsible_depends_on': None,
		'default': '1',
		'depends_on': None,
		'description': None,
		'docstatus': 0L,
		'doctype': 'Custom Field',
		'dt': 'Customer',
		'fieldname': 'tax_id_type',
		'fieldtype': 'Select',
		'hidden': 0,
		'ignore_user_permissions': 0,
		'ignore_xss_filter': 0,
		'in_filter': 0,
		'in_list_view': 0,
		'insert_after': 'territory',
		'label': 'Tax ID Type',
		'no_copy': 0,
		'options': '1\n2\n3',
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