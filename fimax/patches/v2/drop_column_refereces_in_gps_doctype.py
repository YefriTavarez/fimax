import frappe

def execute():
	try:
		frappe.db.sql("alter table `tabGPS Installation` drop column reference_type")
		frappe.db.sql("alter table `tabGPS Installation` drop column reference_name")
	except: pass