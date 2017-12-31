import frappe

def create_desktop_icon(opts):
	opts.doctype = "Desktop Icon"

	icon = opts.icon
	color = opts.color

	del opts.icon
	del opts.color

	if not frappe.db.exists(opts):
		opts.update({
			"icon": icon,
			"color": color,
		})

		return new_desktop_icon(opts)

	existing_doc = frappe.get_doc(opts)
	
	existing_doc.icon = icon
	existing_doc.color = color

	return existing_doc

def new_desktop_icon(opts):
	return frappe.get_doc({
		'doctype': 'Desktop Icon',
		'_doctype': opts.get("_doctype"),
		'_report': None,
		'app': opts.get("app"),
		'blocked': 0,
		'color': opts.get("color"),
		'custom': 1,
		'docstatus': 0L,
		'force_show': 0,
		'hidden': 0,
		'icon': opts.get("icon"),
		'label': opts.get("_doctype"),
		'link': 'List/{doctype}/List'.format(doctype=opts.get("_doctype")),
		'module_name': opts.get("doctype"),
		'reverse': 0,
		'standard': 1,
		'type': 'link'
	})