import frappe

from frappe.utils import flt, cint

def get_capitalization_rate(rate, capitalizations=12):
	"""Calculate using compound interest the capitalization rate"""
	return flt(rate) / cint(capitalizations)

def get_monthly_repayment_amount(amount, rate, periods, capitalizations=12):
	"""Calculate using compound interest the monthly repayment amount"""

	# sanitize args
	periods = cint(periods)
	capitalizations = cint(capitalizations)

	capitalization_rate = get_capitalization_rate(rate, capitalizations)

	# apply formula
	return flt(amount) * flt(capitalization_rate / (1 - (1 + capitalization_rate) ** (- periods)))

def get_total_interest_amount(amount, rate, periods, capitalizations=12):
	"""Calculate using compound interest the total payable interest amount"""
	total_payable_amount = get_total_payable_amount(amount, rate, periods, capitalizations)
	return flt(total_payable_amount) - flt(amount)

def get_total_payable_amount(amount, rate, periods, capitalizations=12):
	"""Calculate using compound interest the total payable amount"""
	monthly_repayment_amount = get_monthly_repayment_amount(amount, rate, periods, capitalizations)
	return cint(periods) * flt(monthly_repayment_amount)

def get_monthly_interest_amount(balance, rate, periods, capitalizations=12):
	"""Calculate using compound interest the monthly interest amount"""
	capitalization_rate = get_capitalization_rate(rate, capitalizations)

	return flt(balance) * flt(capitalization_rate)

def get_monthly_capital(balance, rate, periods, capitalizations=12):
	"""Calculate using compound interest the monthly capital amount"""
	monthly_interest_amount = get_monthly_interest_amount(balance, rate, periods)
	monthly_repayment_amount = get_monthly_repayment_amount(balance, rate, periods)

	return flt(monthly_repayment_amount) - flt(monthly_interest_amount)

def get_total_capital_amount(amount, rate, periods):
	"""Calculate using compound interest the total capital amount"""
	monthly_capital = get_monthly_capital(amount, rate, periods)
	return flt(monthly_capital) * flt(periods)

def get_as_array(amount, rate, periods):
	repayment_schedule = []
	capital_accumulated = 0.000
	interest_accumulated = 0.000
	principal_balance = 0.000

	interest_balance = get_total_interest_amount(amount, rate, periods)
	capital_balance = get_total_capital_amount(amount, rate, periods)
	total_balance = get_total_payable_amount(amount, rate, periods)
	monthly_repayment_amount = get_monthly_repayment_amount(amount, rate, periods)

	periods = cint(periods)
	for period in xrange(periods):

		interest_accumulated += get_monthly_interest_amount(amount, rate, periods)
		capital_accumulated += get_monthly_capital(amount, rate, periods)
		principal_balance += get_monthly_repayment_amount(amount, rate, periods)

		interest_balance -= get_monthly_interest_amount(amount, rate, periods)
		capital_balance -= get_monthly_capital(amount, rate, periods)
		total_balance -= get_monthly_repayment_amount(amount, rate, periods)

		interest = get_monthly_interest_amount(principal_balance, rate, periods)
		capital = get_monthly_capital(principal_balance, rate, periods)

		opts = frappe._dict({
			"interest": interest,
			"capital": capital,
			"monthly_repayment_amount": monthly_repayment_amount,
			"capital_accumulated": capital_accumulated,
			"interest_accumulated": interest_accumulated,
			"interest_balance": interest_balance if interest_balance > 0.000 else 0.000,
			"capital_balance": capital_balance if capital_balance > 0.000 else 0.000,
			"total_balance": total_balance if total_balance > 0.000 else 0.000,
		})

		repayment_schedule.append(opts)
	return repayment_schedule
