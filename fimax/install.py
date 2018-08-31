import frappe

def before_install():
	"""runs before installation"""
	return check_setup_wizard_is_completed()


def after_install():
	"""runs after installation"""
	add_reqd_roles()
	add_default_loan_charges_type()
	add_reqd_custom_fields()
	add_translations()

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

		if loan_charges_type in ["Insurance", "GPS", "Late Payment Fee"]:
			doc = create_loan_charges_type(loan_charges_type, repayment_frequency="Yearly")
			doc.generates_fine = 0
		else:
			doc = create_loan_charges_type(loan_charges_type)

		doc.save()

def add_reqd_custom_fields():
	from fimax.hook.custom_field import add_reqd_custom_fields_in_user
	from fimax.hook.custom_field import add_reqd_custom_fields_in_company
	from fimax.hook.custom_field import add_reqd_custom_fields_in_customer
	
	add_reqd_custom_fields_in_user()
	add_reqd_custom_fields_in_company()
	add_reqd_custom_fields_in_customer()
	
def update_erpnext_icons():
	"""removes default apps' icon from desktop"""

	customer_icons = frappe.get_list("Desktop Icon", {
		"module_name": "Customer",
	}, ["name"])


	todo_icons = frappe.get_list("Desktop Icon", {
		"module_name": "ToDo",
	}, ["name"])

	for icon in customer_icons:
		doc = frappe.get_doc("Desktop Icon", icon)
		doc.update({
			"color": "#469",
			"icon": "fa fa-user-circle-o",
			"type": "link",
			"link": "List/Customer/List"
		})

		doc.db_update()
	
	for icon in todo_icons:
		doc = frappe.get_doc("Desktop Icon", icon)
		doc.update({
			"icon": "fa fa-check",
			"type": "link",
			"link": "List/ToDo/List"
		})

		doc.db_update()
	
	# save the changes to the database
	frappe.db.commit()

def check_setup_wizard_is_completed():
	if not frappe.db.get_default('desktop:home_page') == 'desktop':
		print()
		print("Fimax cannot be installed on a fresh site where the setup wizard is not completed")
		print("You can run the setup wizard and come back to finish with the installation")
		print()
		return False

def add_translations():
	import csv, os, subprocess

	current_directory = subprocess.check_output("pwd")

	os.chdir("../apps/fimax/fimax")

	translation_file = open("translations.csv", "r")

	os.chdir(current_directory.replace("\n",""))

	csv_file_reader = csv.reader(translation_file)

	for idx, (source, translated) in enumerate(csv_file_reader):
	    if not idx: continue 

	    if frappe.db.exists("Translation", {
	    	"source_name": source,
	    	"language": "es",
	    }): continue

	    doc = frappe.new_doc("Translation")
	    doc.language = "es"
	    doc.source_name = source
	    doc.target_name = translated
	    
	    doc.insert()

	frappe.db.commit()
