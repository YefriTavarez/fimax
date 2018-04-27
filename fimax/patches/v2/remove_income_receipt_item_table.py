import frappe

def execute():
	frappe.db.sql("""DROP TABLE IF EXISTS `tabIncome Receipt Item`""")