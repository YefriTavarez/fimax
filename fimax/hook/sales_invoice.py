import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as SalesInvoiceERPNext
from fimax.utils import validate_comment_on_cancel

class SalesInvoice(SalesInvoiceERPNext):
    def on_cancel(self):
        super(SalesInvoice, self).on_cancel()
        user = frappe.session.user
        validate_comment_on_cancel(user=user, doctype=self.doctype, docname=self.name)