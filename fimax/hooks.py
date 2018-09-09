# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "fimax"
app_title = "Fi-Max"
app_publisher = "Yefri Tavarez"
app_description = "Manage your finances with the best manager"
app_icon = "fa fa-superpowers"
app_color = "#469"
app_email = "yefritavarez@gmail.com"
app_license = "General Public License v3"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/css/fimax.min.css"
app_include_js = "/assets/js/fimax.min.js"

# include js, css files in header of web template
web_include_css = "/assets/fimax/css/web_fimax.css"
web_include_js = "/assets/fimax/js/web_fimax.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"DocType" : "public/js/doctype.js",
	"Customer" : [
		"public/js/customer.js",
		"public/js/jquery.mask.min.js",
	],
	"Supplier" : "public/js/supplier.js",
	"Employee" : "public/js/employee.js",
	"Company" : [
		"public/js/company.js",
		"public/js/jquery.mask.min.js",
	],
	"User" : "public/js/user.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "desk"

# website user home page (by Role)
role_home_page = {
	"All": "desk",
	"Guest": "login"
}

# Website user home page (by function)
# get_website_user_home_page = "fimax.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

before_install = "fimax.install.before_install"
after_install = "fimax.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

notification_config = "fimax.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Customer": {
		"validate": "fimax.hook.customer.validate",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"fimax.scheduler.all"
	],
	"daily": [
		"fimax.scheduler.daily"
	],
	"hourly": [
		"fimax.scheduler.hourly"
	],
	"weekly": [
		"fimax.scheduler.weekly"
	],
	"monthly": [
		"fimax.scheduler.monthly"
	]
}

# Testing
# -------

# before_tests = "fimax.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------

override_whitelisted_methods = {
	"frappe.desk.notifications.get_notifications": "fimax.notifications.get_notifications"
}

boot_session = "fimax.boot.get_boot_info"
