import frappe

from frappe.utils import flt, cint

def get_capitalization_rate(rate, capitalizations=12):
	"""Calculate using compound interest the capitalization rate"""
	return flt(rate) / cint(capitalizations)

def get_repayment_amount(amount, rate, periods, capitalizations=12):
	"""Calculate using compound interest the repayment amount"""

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
	repayment_amount = get_repayment_amount(amount, rate, periods, capitalizations)
	return cint(periods) * flt(repayment_amount)

def get_interest_amount(balance, rate, periods, capitalizations=12):
	"""Calculate using compound interest the interest amount"""
	capitalization_rate = get_capitalization_rate(rate, capitalizations)

	return flt(balance) * flt(capitalization_rate)

def get_capital_amount(balance, rate, periods, capitalizations=12):
	"""Calculate using compound interest the capital amount"""
	interest_amount = get_interest_amount(balance, rate, periods)
	repayment_amount = get_repayment_amount(balance, rate, periods)

	return flt(repayment_amount) - flt(interest_amount)

def get_total_capital_amount(amount, rate, periods):
	"""Calculate using compound interest the total capital amount"""
	return flt(amount) * flt(1.0000)

def get_as_array(amount, rate, periods):
	repayment_schedule = []
	capital_accumulated = 0.000
	interest_accumulated = 0.000
	principal_balance = 0.000

	interest_balance = get_total_interest_amount(amount, rate, periods)
	capital_balance = get_total_capital_amount(amount, rate, periods)
	total_balance = get_total_payable_amount(amount, rate, periods)
	repayment_amount = get_repayment_amount(amount, rate, periods)

	periods = cint(periods)
	for period in xrange(periods):

		interest_amount = get_interest_amount(capital_balance, rate, periods)
		capital_amount = repayment_amount - interest_amount

		interest_accumulated += interest_amount
		capital_accumulated += capital_amount
		principal_balance += repayment_amount

		interest_balance -= interest_amount
		capital_balance -= capital_amount
		total_balance -= repayment_amount

		opts = frappe._dict({
			"idx": period +1,
			"interest_amount": interest_amount,
			"capital_amount": capital_amount,
			"repayment_amount": repayment_amount,
			"principal_balance": principal_balance,
			"capital_accumulated": capital_accumulated,
			"interest_accumulated": interest_accumulated,
			"interest_balance": interest_balance if interest_balance > 0.000 else 0.000,
			"capital_balance": capital_balance if capital_balance > 0.000 else 0.000,
			"total_balance": total_balance if total_balance > 0.000 else 0.000,
		})

		repayment_schedule.append(opts)
	return repayment_schedule
