# Copyright (c) 2022, Miguel Higuera, Christopher Martinez and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    return get_columns(), get_data(filters)


def get_columns():
    return [
        _('Loan:Link/Loan:130'),
        _('Customer:Link/Customer:200'),
        _('Phone:Data:150'),
        _('Fecha de Cuota:Date:150'),
        _(' # Cuota:Data:70'),
        _('Pagare:Currency:150'),
        _('Monto Pagado:Currency:150'),
        _('Monto Pendiente:Currency:150'),
        _('Estado Cuota:Data:150'),

        _('Address:Data:200'),
        _('City:Data:100'),
        _('Posting Date:Date:120'),
        _('Total del Prestamo:Currency:150'),
        _('Insurance Amount:Currency:150'),
        _('GPS Amount:Currency:150'),
        _('Capital:Currency:150'),
        _('Comision:Currency:150'),
        # _('Fine Amount:Currency:150'),
        _('Estado Prestamo:Data:150'),
    ]


def get_data(filters):
    # conditions = ["`tabLoan Repayment Schedule`.status != 'Paid'"]
    conditions = []

    if filters.get('from_date'):
        condition = f"`tabLoan Repayment Schedule`.repayment_date >= '{filters.from_date}'"
        if filters.get("filter_dates_on") == "Loan":
            condition = f"`tabLoan`.posting_date >= '{filters.from_date}'"
        conditions.append(condition)

    if filters.get('to_date'):
        condition = f"`tabLoan Repayment Schedule`.repayment_date <= '{filters.to_date}'"
        if filters.get("filter_dates_on") == "Loan":
            condition = f"`tabLoan`.posting_date <= '{filters.to_date}'"
        conditions.append(condition)

    if filters.get('customer_name'):
        conditions.append(f"`tabCustomer`.name = '{filters.customer_name}'")

    if filters.get('loan'):
        conditions.append(f"`tabLoan`.name = '{filters.loan}'")

    if filters.get('status'):
        conditions.append(
            f"`tabLoan Repayment Schedule`.status = '{filters.status}'")

    conditions = " and ".join(conditions or ['1=1'])

    data = frappe.db.sql("""
    SELECT
      `tabLoan`.name,                                                       #0
      `tabCustomer`.name,                                                   #1
      `tabAddress`.phone,                                                   #2
      `tabLoan Repayment Schedule`.repayment_date,                          #3
      `tabLoan Charges`.repayment_period,                                   #4
      `tabLoan Repayment Schedule`.repayment_amount,                        #5
      `tabLoan Repayment Schedule`.paid_amount,                             #6
      `tabLoan Repayment Schedule`.outstanding_amount,                      #7
      `tabLoan Repayment Schedule`.status,                                  #8

      `tabAddress`.address_line1,                                           #9
      `tabAddress`.city,                                                   #10
      `tabLoan`.posting_date,                                              #11
      `tabLoan`.total_payable_amount,                                      #12
      `tabLoan Application`.insurance_amount,                              #13
      `tabLoan Application`.gps_amount,                                    #14
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Capital',
              `tabLoan Charges`.outstanding_amount,
              0
          )
          
      ) AS 'Capital',                                                      #15
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Interest',
              `tabLoan Charges`.outstanding_amount,
              0
          )
          
      ) AS 'Comision',                                                     #16
      `tabLoan`.status AS loan_status                                      #17
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
        `tabLoan Repayment Schedule`.repayment_date
        
    """.format(conditions=conditions), as_list=True)

    # clear repeated data for loans
    previous_loan = None

    for row in data:
        # don't touch this as this is the loan_id
        # which is used to organize the data
        loan = row[0]

        # translate the status (the two of them)
        row[8] = _(row[8])  # repayment status
        row[17] = _(row[17])  # loan status

        # clear the first three columns
        # - loan_id, customer and customer phone
        if loan == previous_loan:
            for idx in range(0, 3):
                row[idx] = None

            # clear total_payable_amount
            row[9] = None  # address
            row[10] = None  # city
            row[11] = None  # posting_date
            row[12] = None  # total_payable_amount
            row[13] = None  # insurance_amount
            row[14] = None  # gps_amount
            row[17] = None  # loan_status

        previous_loan = loan

    return data
