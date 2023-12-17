# -*- coding: utf-8 -*-
# Copyright (c) 2022, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

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
def loan_charges_query(doctype, txt, searchfield, start, page_len, filters):
	from frappe.query_builder import Criterion
	conditions = []
	LC = frappe.qb.DocType("Loan Charges")
	LCT = frappe.qb.DocType("Loan Charges Type")
	
	if filters and filters.get("loan"):
		conditions.append(LC.loan == filters.get("loan"))
	
	if filters and filters.get("status"):
		conditions.append(~LC.status.isin(filters.get("status")))
	
	if filters and filters.get("docstatus"):
		conditions.append(LC.docstatus == filters.get("docstatus"))
	
	if filters and filters.get("custom_filters"):
		custom_filters = filters.get("custom_filters")
		if custom_filters.get("search_term"):
			conditions.append(LC.name.like("%{0}%".format(custom_filters.get("search_term"))))
		if custom_filters.get("repayment_period"):
			conditions.append(LC.repayment_period == custom_filters.get("repayment_period"))
		if custom_filters.get("loan_charges_type"):
			conditions.append(LC.loan_charges_type == custom_filters.get("loan_charges_type"))
	
	return frappe.qb.from_(LC).join(LCT).on(
			LC.loan_charges_type == LCT.name
		).select(
			LC.name,
			LC.loan,
			LC.loan_charges_type,
			LC.repayment_period,
			LC.status
		).where(
			Criterion.all(conditions)
		).orderby(LC.loan, LC.repayment_period, LCT.priority).run(as_dict=True)

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
