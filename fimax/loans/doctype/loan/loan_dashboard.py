from frappe import _

def get_data():
	return {
		'fieldname': 'loan',
		'non_standard_fieldnames': {
			# 'Delivery Note': 'against_sales_order',
			# 'Journal Entry': 'reference_name',
			# 'Payment Entry': 'reference_name',
			# 'Payment Request': 'reference_name',
			# 'Subscription': 'reference_document',
		},
		'internal_links': {
			# 'Loan Application': ['items', 'prevdoc_docname']
		},
		'transactions': [
			{
				'label': _('Insurance and GPS'),
				'items': ['Insurance Card', 'GPS Installation']
			},
			{
				'label': _('Legal'),
				'items': ['Loan Terms and Conditions']
			},
			{
				'label': _('Payments'),
				'items': ['Loan Charges', 'Income Receipt']
			},
			{
				'label': _('Records'),
				'items': ['Loan Record']
			},
		]
	}