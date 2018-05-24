import frappe

def before_install():
	"""runs before installation"""
	add_reqd_roles()

def after_install():
	"""runs after installation"""
	# update_customer_icons()
	add_default_loan_charges_type()
	add_reqd_custom_fields()

def add_reqd_roles():
	"""adds default roles for the app to run"""

	from fimax.hook.role import create_simple_role
	role_list = ["Loan Approver", "Loan Manager", "Loan User", "CEO", 
		"Cashier", "General Manager", "Finance Manager", "Finance User",
		"Collector User", "Collector Manager"]

	for role in role_list:
		if frappe.db.exists("Role", role): 
			continue

		doc = create_simple_role(role)
		doc.save()

	# save the changes to the database
	frappe.db.commit()

def add_default_loan_charges_type():
	"""adds default loan charges type for the app to run"""
	from fimax.hook.loan_charges_type import create_loan_charges_type

	loan_charges_type_list = ["Capital", "Interest", "Repayment Amount",
		"Insurance", "Late Payment Fee", "GPS"]

	for loan_charges_type in loan_charges_type_list:
		if frappe.db.exists("Loan Charges Type", loan_charges_type):
			continue

		if loan_charges_type in ["Insurance", "GPS"]:
			doc = create_loan_charges_type(loan_charges_type, repayment_frequency="Yearly")
		else:
			doc = create_loan_charges_type(loan_charges_type)

		doc.save()

def add_reqd_custom_fields():
	from fimax.hook.custom_field import add_reqd_custom_fields_in_company
	add_reqd_custom_fields_in_company()
	
def update_customer_icons():
	"""removes default apps' icon from desktop"""

	customer_icons = frappe.get_list("Desktop Icon", {
		"module_name": "Customer",
	}, ["name"])

	update_them(customer_icons)

def update_them(icon_list):
	"""hide a list of icons"""
	
	doctype = "Desktop Icon"

	for icon in icon_list:
		doc = frappe.get_doc(doctype, icon)
		doc.update({
			"color": "#469",
			"icon": "fa fa-user-circle-o",
			"type": "link",
			"link": "List/Customer/List"
		})

		doc.db_update()
	
	# save the changes to the database
	frappe.db.commit()
