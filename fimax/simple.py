import frappe

from frappe.utils import flt, cint

def get_total_interest_amount(amount, rate, periods):
	"""Calculate using simple interest the total payable interest amount"""
	# frappe.msgprint(f"amount: {flt(amount) * flt(rate) * flt(periods)}")
	return flt(amount) * flt(rate) * flt(periods)

def get_total_payable_amount(amount, rate, periods):
	"""Calculate using simple interest the total payable amount"""
	total_interest = get_total_interest_amount(amount, rate, periods)
	return flt(total_interest) + flt(amount)

def get_interest_amount(amount, rate, periods):
	"""Calculate using simple interest the interest amount"""
	total_interest_amount = get_total_interest_amount(amount, rate, periods)
	return flt(total_interest_amount) / flt(periods)

def get_repayment_amount(amount, rate, periods):
	"""Calculate using simple interest the repayment amount"""
	total_payable_amount = get_total_payable_amount(amount, rate, periods)
	# frappe.msgprint(f" amount: {total_payable_amount / periods}")
	return flt(total_payable_amount) / flt(periods)

def get_capital_amount(amount, rate, periods):
	"""Calculate using simple interest the capital amount"""
	interest_amount = get_interest_amount(amount, rate, periods)
	repayment_amount = get_repayment_amount(amount, rate, periods)
	return flt(repayment_amount) - flt(interest_amount)

def get_total_capital_amount(amount, rate, periods):
	"""Calculate using simple interest the total capital amount"""
	capital_amount = get_capital_amount(amount, rate, periods)
	return flt(capital_amount) * flt(periods)

def get_as_array(amount, rate, periods):
	repayment_schedule = []
	capital_accumulated = 0.000
	interest_accumulated = 0.000
	principal_balance = 0.000

	interest_amount = get_interest_amount(amount, rate, periods)
	capital_amount = get_capital_amount(amount, rate, periods)
	repayment_amount = get_repayment_amount(amount, rate, periods)

	interest_balance = get_total_interest_amount(amount, rate, periods)
	capital_balance = get_total_capital_amount(amount, rate, periods)
	total_balance = get_total_payable_amount(amount, rate, periods)

	periods = cint(periods)
	for period in range(periods):

		interest_accumulated += get_interest_amount(amount, rate, periods)
		capital_accumulated += get_capital_amount(amount, rate, periods)
		principal_balance += get_repayment_amount(amount, rate, periods)

		interest_balance -= get_interest_amount(amount, rate, periods)
		capital_balance -= get_capital_amount(amount, rate, periods)
		total_balance -= get_repayment_amount(amount, rate, periods)

		opts = frappe._dict({
			"idx": period + 1,
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
