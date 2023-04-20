SUM(
          IF(
              `tabLoan Charges`.loan_charges_type = 'Late Payment Fee',
              `tabLoan Charges`.outstanding_amount,
                0
            )
      ) AS 'Fine Amount',