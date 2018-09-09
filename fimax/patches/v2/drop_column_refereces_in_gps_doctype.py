import frappe

def execute():
	for fieldname in ("reference_type", "reference_name"):
		try:
			frappe.db.sql("alter table `tabGPS Installation` drop column {0}".format(fieldname))
		except: 
			pass
