import frappe

def execute():
	try:
		frappe.db.sql("update `tabGPS Installation` set start_date = starts_date where start_date is null")
	except: pass

	try:
		frappe.db.sql("alter table `tabGPS Installation` drop column starts_date")
	except: pass

