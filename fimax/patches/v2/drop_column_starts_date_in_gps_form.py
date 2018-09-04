import frappe

def execute():
	try:
		frappe.db.sql("alter table `tabGPS Installation` drop column starts_date")
	except:
		pass