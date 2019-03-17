import frappe

def get_notification_config():
	return {
		"for_doctype": {
			"Loan": "fimax.notifications.loans",
			"Loan Application": { "status": "Open" },
			"Loan Record": "fimax.notifications.loan_records",
			# "Loan Application": "fimax.notifications.loan_appls",
		}
	}

def loans(as_list=False):
	if not frappe.has_permission("Income Receipt", "submit"):
		return 0.000

	data = frappe.get_list("Loan", {
		"status": ["in", ["Open", "Legal"]]
	}, ["name"])

	return data if as_list else len(data)

def loan_records(as_list=False):
	if not frappe.has_permission("Income Receipt", "submit"):
		return 0.000

	data = frappe.get_list("Loan Record", {
		"status": ["in", ["Open", "Legal"]]
	}, ["name"])

	return data if as_list else len(data)

def loan_appls(as_list=False):
	if not frappe.has_permission("Loan", "submit"):
		return 0.000

	data = frappe.get_list("Loan Application", {
		"status": ["=", "Open"]
	}, ["name"])

	return data if as_list else len(data)

@frappe.whitelist(allow_guest=True)
def get_notifications():

	if frappe.flags.in_install:
		return
		
	# if user has no permission
	if frappe.session.user == "Guest":
		return {
			"open_count_doctype": 0,
			"open_count_module": 0,
			"open_count_other": 0,
			"targets": 0,
			"new_messages": 0,
		}
		
	from frappe.desk.notifications import get_notification_config
	config = get_notification_config()

	groups = list(config.get("for_doctype").keys()) + list(config.get("for_module").keys())
	cache = frappe.cache()

	notification_count = {}
	notification_percent = {}

	for name in groups:
		count = cache.hget("notification_count:" + name, frappe.session.user)
		if count is not None:
			notification_count[name] = count

	from frappe.desk.notifications import get_notifications_for_doctypes
	from frappe.desk.notifications import get_notifications_for_modules
	from frappe.desk.notifications import get_notifications_for_other
	from frappe.desk.notifications import get_notifications_for_targets
	from frappe.desk.notifications import get_new_messages

	return {
		"open_count_doctype": get_notifications_for_doctypes(config, notification_count),
		"open_count_module": get_notifications_for_modules(config, notification_count),
		"open_count_other": get_notifications_for_other(config, notification_count),
		"targets": get_notifications_for_targets(config, notification_percent),
		"new_messages": get_new_messages()
	}
