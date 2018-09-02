import frappe

def execute():
	passed = True

	try:
		# let's make sure that this table exists
		frappe.db.sql("select name from  `tabLoan Record`")
	except:
		passed = False

	if not passed: return

	frappe.db.sql("""update `tabLoan Record` 
		set status = 'Disbursed' where status = 'Normal'""")