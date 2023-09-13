import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry as PaymentEntryERPNext
from fimax.utils import validate_comment_on_cancel

class PaymentEntry(PaymentEntryERPNext):
    def on_cancel(self):
        super(PaymentEntry, self).on_cancel()
        user = frappe.session.user
        validate_comment_on_cancel(user=user, doctype=self.doctype, docname=self.name)