# Copyright (c) 2023, Yefri Tavarez and contributors
# For license information, please see license.txt
import frappe

def get_repayment_status(loan_charges):
    has_overdue = any(charge.status == 'Overdue' for charge in loan_charges)
    if has_overdue:
        return 'Overdue'
    
    has_partially_paid = any(charge.status == 'Partially' for charge in loan_charges)
    if has_partially_paid:
        return 'Partially'
    
    has_pending = any(charge.status == 'Pending' for charge in loan_charges)
    if has_pending:
        return 'Pending'
    
    all_paid = all(charge.status == 'Paid' for charge in loan_charges)
    if all_paid:
        return 'Paid'
    
    return 'Unknown'  # Default to 'Paid' if no other status matches
