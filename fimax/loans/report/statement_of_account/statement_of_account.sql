update
  `tabLoan Repayment Schedule` set repayment_date = '2023-01-05'
where	
  `tabLoan Repayment Schedule`.parent = "LOAN-00003"
  AND `tabLoan Repayment Schedule`.idx < 14



