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
        _('Descuento:Currency:150'),
        _('Monto Neto:Currency:150'),
        _('Monto Pendiente:Currency:150'),
        _('Estado Cuota:Data:150'),

        _('Address:Data:200'),
        _('City:Data:100'),
        _('Posting Date:Date:120'),
        # _('Cuota:Currency:150'),
        _('Insurance Amount:Currency:150'),
        # _('GPS Amount:Currency:150'),
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
        SUM(
            IF(
              (`tabLoan Charges`.loan_charges_type = 'Insurance' AND `tabLoan Charges`.reference_type = 'Insurance Card'),
              0,
              `tabLoan Charges`.paid_amount
          )
        ) AS 'paid_amount',                                                 #6
        SUM(`tabLoan Charges`.discount_amount) as 'discount',               #7
        (SUM(
          IF(
              (`tabLoan Charges`.loan_charges_type = 'Insurance' AND `tabLoan Charges`.reference_type = 'Insurance Card'),
              0,
              `tabLoan Charges`.paid_amount
          )
      ) - SUM(`tabLoan Charges`.discount_amount)) as 'net_amount', # 8
        SUM(
            IF(
              (`tabLoan Charges`.loan_charges_type = 'Insurance' AND `tabLoan Charges`.reference_type = 'Insurance Card'),
              0,
              `tabLoan Charges`.outstanding_amount
          )
        ) AS 'outstanding_amount' ,                                         #9     
      `tabLoan Repayment Schedule`.status,                                  #10
      `tabAddress`.address_line1,                                           #11
      `tabAddress`.city,                                                   #12
      `tabLoan`.posting_date,                                              #13

      
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Insurance',
              `tabLoan Charges`.outstanding_amount,
              0
          )
          
      ) AS 'Insurance',           #15
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Capital',
              `tabLoan Charges`.outstanding_amount,
              0
          )                               #15
      SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Interest',
              `tabLoan Charges`.outstanding_amount,
              0
          )
          
      ) AS 'Comision',                     
      ) AS 'Capital',                                                       #16
      `tabLoan`.status AS loan_status                                      #17
    FROM 
        `tabCustomer`

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
        `tabLoan Repayment Schedule`.idx = `tabLoan Charges`.repayment_period
    AND
        `tabLoan Repayment Schedule`.parent = `tabLoan Charges`.loan
    LEFT JOIN 
        `tabDynamic Link`
    ON
        `tabCustomer`.name = `tabDynamic Link`.link_name
        AND
        `tabDynamic Link`.link_doctype = 'Customer'
        AND
        `tabDynamic Link`.parenttype = 'Address'
        AND
        `tabDynamic Link`.parentfield = 'links'
        
    LEFT JOIN 
        `tabAddress`
    ON
        `tabAddress`.name = `tabDynamic Link`.parent
    WHERE
        {conditions}
    GROUP BY
        `tabLoan`.name,
        `tabLoan Charges`.repayment_period
    ORDER BY
        `tabLoan`.name,
        `tabLoan Charges`.repayment_period,
        `tabLoan Repayment Schedule`.repayment_date
        
    """.format(conditions=conditions), as_list=True, debug=True)

    # clear repeated data for loans
    previous_loan = None

    for row in data:
        # don't touch this as this is the loan_id
        # which is used to organize the data
        loan = row[0]

        # translate the status (the two of them)
        row[9] = _(row[9])  # repayment status
        row[17] = _(row[17])  # loan status

        # clear the first three columns
        # - loan_id, customer and customer phone
        if loan == previous_loan:
            for idx in range(0, 3):
                row[idx] = None

            # clear total_payable_amount
            row[11] = None  # address
            row[12] = None  # city
            row[13] = None  # posting_date
            # row[13] = None  # total_payable_amount
            #row[14] = None  # insurance_amount
            # row[15] = None  # gps_amount
            row[17] = None  # loan_status

        previous_loan = loan

    return data
