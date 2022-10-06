import frappe

from erpnext.controllers.queries import get_match_cond


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def loan_linked_application_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""select name, party_type, party_name, company from `tabLoan Application`
		where docstatus < 2
			and status = 'Approved'
			and name in (select tabLoan.loan_application 
				from tabLoan 
					where 
						tabLoan.loan_application = `tabLoan Application`.name 
					and 
						tabLoan.docstatus < 2)
			and ({key} like %(txt)s
				or party_type like %(txt)s
				or party_name like %(txt)s
				or company like %(txt)s)
			{mcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, party_type), locate(%(_txt)s, party_type), 99999),
			if(locate(%(_txt)s, party_name), locate(%(_txt)s, party_name), 99999),
			if(locate(%(_txt)s, company), locate(%(_txt)s, company), 99999),
			name, party_name
		limit %(start)s, %(page_len)s""".format(**{
        'key': searchfield,
        'mcond': get_match_cond(doctype)
    }), {
        'txt': "%%%s%%" % txt,
        '_txt': txt.replace("%", ""),
        'start': start,
        'page_len': page_len
    })


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def loan_unlinked_application_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""select name, party_type, party_name, company from `tabLoan Application`
		where docstatus < 2
			and status = 'Approved'
			and name not in (select tabLoan.loan_application 
				from tabLoan 
					where 
						tabLoan.loan_application = `tabLoan Application`.name 
					and 
						tabLoan.docstatus < 2)
			and ({key} like %(txt)s
				or party_type like %(txt)s
				or party_name like %(txt)s
				or company like %(txt)s)
			{mcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, party_type), locate(%(_txt)s, party_type), 99999),
			if(locate(%(_txt)s, party_name), locate(%(_txt)s, party_name), 99999),
			if(locate(%(_txt)s, company), locate(%(_txt)s, company), 99999),
			name, party_name
		limit %(start)s, %(page_len)s""".format(**{
        'key': searchfield,
        'mcond': get_match_cond(doctype)
    }), {
        'txt': "%%%s%%" % txt,
        '_txt': txt.replace("%", ""),
        'start': start,
        'page_len': page_len
    })


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_loans(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""SELECT 
			`tabLoan`.name, 
			`tabLoan`.party_type,
			`tabLoan`.party, 
			`tabLoan`.party_name 
		FROM `tabLoan`
		INNER JOIN `tabCustom Loan`
			ON `tabLoan`.loan_type = `tabCustom Loan`.name
		WHERE `tabCustom Loan`.asset_type = %(asset_type)s
			AND ({key} LIKE %(txt)s)
			{mcond}
		ORDER BY
			if(locate(%(_txt)s, `tabLoan`.name), locate(%(_txt)s, `tabLoan`.name), 99999),
			if(locate(%(_txt)s, `tabLoan`.party), locate(%(_txt)s, `tabLoan`.party), 99999),
			if(locate(%(_txt)s, `tabLoan`.party_name), locate(%(_txt)s, `tabLoan`.party_name), 99999),
			`tabLoan`.name, `tabLoan`.party
		LIMIT %(start)s, %(page_len)s""".format(**{
        'key': "`tab{0}`.{1}".format(doctype, searchfield),
        'mcond': get_match_cond(doctype)
    }), {
        'txt': "%%%s%%" % txt,
        '_txt': txt.replace("%", ""),
        'start': start,
        'page_len': page_len,
        'asset_type': filters.get("asset_type")
    })
