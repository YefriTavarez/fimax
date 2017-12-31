import frappe

from frappe.utils import flt, cint

def get_total_interest_amount(amount, rate, periods):
	"""Calculate using simple interest the total payable interest amount"""
	return flt(amount) * flt(rate) * flt(periods)

def get_total_payable_amount(amount, rate, periods):
	"""Calculate using simple interest the total payable amount"""
	total_interest = get_total_interest_amount(amount, rate, periods)
	return flt(total_interest) + flt(amount)

def get_monthly_interest_amount(amount, rate, periods):
	"""Calculate using simple interest the monthly interest amount"""
	total_interest_amount = get_total_interest_amount(amount, rate, periods)
	return flt(total_interest_amount) / flt(periods)

def get_monthly_repayment_amount(amount, rate, periods):
	"""Calculate using simple interest the monthly repayment amount"""
	total_payable_amount = get_total_payable_amount(amount, rate, periods)
	return flt(total_payable_amount) / flt(periods)

def get_monthly_capital(amount, rate, periods):
	"""Calculate using simple interest the monthly capital amount"""
	monthly_interest_amount = get_monthly_interest_amount(amount, rate, periods)
	monthly_repayment_amount = get_monthly_repayment_amount(amount, rate, periods)
	return flt(monthly_repayment_amount) - flt(monthly_interest_amount)

def get_total_capital_amount(amount, rate, periods):
	"""Calculate using simple interest the total capital amount"""
	monthly_capital = get_monthly_capital(amount, rate, periods)
	return flt(monthly_capital) * flt(periods)

def get_as_array(amount, rate, periods):
	repayment_schedule = []
	capital_accumulated = 0.000
	interest_accumulated = 0.000

	interest = get_monthly_interest_amount(amount, rate, periods)
	capital = get_monthly_capital(amount, rate, periods)
	monthly_repayment_amount = get_monthly_repayment_amount(amount, rate, periods)

	interest_balance = get_total_interest_amount(amount, rate, periods)
	capital_balance = get_total_capital_amount(amount, rate, periods)
	total_balance = get_total_payable_amount(amount, rate, periods)

	periods = cint(periods)
	for period in xrange(periods):

		interest_accumulated += get_monthly_interest_amount(amount, rate, periods)
		capital_accumulated += get_monthly_capital(amount, rate, periods)

		interest_balance -= get_monthly_interest_amount(amount, rate, periods)
		capital_balance -= get_monthly_capital(amount, rate, periods)
		total_balance -= get_monthly_repayment_amount(amount, rate, periods)

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
