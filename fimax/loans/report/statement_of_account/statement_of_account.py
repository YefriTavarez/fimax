# Copyright (c) 2022, Miguel Higuera, Christopher Martinez and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    return get_columns(), get_data(filters)


def get_columns():
    return [
        _('Customer:Link/Customer:200'),
        _('Customer Type:Data:150'),
        _('Phone:Data:150'),
        _('Address:Data:200'),
        _('City:Data:100'),
        _('Loan:Link/Loan:150'),
        _('Posting Date:Date:120'),
        _('Status:Data:150'),
        _('Total Payable Amount:Currency:150'),
        _('Insurance Amount:Currency:150'),
        _('GPS Amount:Currency:150'),
        _('Repayment Period:Int:150'),
        _('Repayment Date:Date:150'),
        _('Repayment Amount:Currency:150'),
        _('Outstanding Amount:Currency:150'),
        _('Capital:Currency:150'),
        _('Interest:Currency:150'),
        _('Fine Amount:Currency:150'),
        _('R. Status:Data:150'),
    ]


def get_data(filters):
    conditions = []

    if filters.get('from_date'):
        conditions.append(f"`tabLoan`.posting_date >= '{filters.from_date}'")

    if filters.get('to_date'):
        conditions.append(f"`tabLoan`.posting_date <= '{filters.to_date}'")

    if filters.get('customer_name'):
        conditions.append(f"`tabCustomer`.name = '{filters.customer_name}'")

    if filters.get('loan'):
        conditions.append(f"`tabLoan`.name = '{filters.loan}'")

    if filters.get('status'):
        conditions.append(f"`tabLoan Repayment Schedule`.status = '{filters.status}'")

    # if filters.get('status'):
    #     conditions.append(f"`tabLoan`.status = '{filters.status}'")

    # if filters.get('city'):
    #     conditions.append(f"`tabAddress`.city LIKE '{filters.city}%'")

    conditions = " and ".join(conditions or ['1=1'])

    data = frappe.db.sql("""
    SELECT
      `tabCustomer`.name,
      `tabCustomer`.customer_type,
      `tabAddress`.phone,
      `tabAddress`.address_line1,
      `tabAddress`.city,
      `tabLoan`.name,
      `tabLoan`.posting_date,
      `tabLoan`.status AS loan_status,
      `tabLoan`.total_payable_amount,
      `tabLoan Application`.insurance_amount,
      `tabLoan Application`.gps_amount,
      `tabLoan Charges`.repayment_period,
      `tabLoan Repayment Schedule`.repayment_date,
      `tabLoan Repayment Schedule`.repayment_amount,
      `tabLoan Repayment Schedule`.outstanding_amount,
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Capital',
              `tabLoan Charges`.outstanding_amount,
              0
          )
          
      ) AS 'Capital',
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Interest',
              `tabLoan Charges`.outstanding_amount,
              0
          )
          
      ) AS 'Interest',
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Late Payment Fee',
              `tabLoan Charges`.outstanding_amount,
                0
            )
      ) AS 'Fine Amount',
      `tabLoan Repayment Schedule`.status
    FROM 
        `tabCustomer`
    INNER JOIN 
        `tabDynamic Link`
    ON
        `tabCustomer`.name = `tabDynamic Link`.link_name
        AND
        `tabDynamic Link`.link_doctype = 'Customer'
        AND
        `tabDynamic Link`.parenttype = 'Address'
        AND
        `tabDynamic Link`.parentfield = 'links'
        
    INNER JOIN 
        `tabAddress`
    ON
        `tabAddress`.name = `tabDynamic Link`.parent
    INNER JOIN
        `tabLoan`
    ON
        `tabCustomer`.name = `tabLoan`.party
        AND
        `tabLoan`.party_type = 'Customer'
    INNER JOIN
        `tabLoan Application`
    ON    
        `tabLoan Application`.name = `tabLoan`.loan_application  
    INNER JOIN
        `tabLoan Charges`
    ON
        `tabLoan`.name = `tabLoan Charges`.loan
        AND 
        `tabLoan Charges`.docstatus = 1
        AND
        `tabLoan`.docstatus = 1
    INNER JOIN
        `tabLoan Repayment Schedule`
    ON
        `tabLoan Repayment Schedule`.name = `tabLoan Charges`.reference_name
    WHERE
        {conditions}
    GROUP BY
        `tabLoan`.name,
        `tabLoan Repayment Schedule`.name
    ORDER BY
        `tabLoan`.name,
        `tabLoan Charges`.repayment_period;
    """.format(conditions=conditions), as_list=True)

    previous_loan = None

    for row in data:
        loan = row[5]
        if loan == previous_loan:
            for idx in range(0, 11):
                row[idx] = None

        previous_loan = loan

    return data
