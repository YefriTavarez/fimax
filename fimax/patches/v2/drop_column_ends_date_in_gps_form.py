import frappe

def execute():
	try:
		frappe.db.sql("update `tabGPS Installation` set end_date = ends_date")
	except: pass
	
	try:
		frappe.db.ddl_sql("alter table `tabGPS Installation` drop column ends_date")
	except: pass
