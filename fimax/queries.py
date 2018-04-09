import frappe

from erpnext.controllers.queries import get_match_cond

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
