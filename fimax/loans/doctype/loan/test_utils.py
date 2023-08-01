# Copyright (c) 2023, Yefri Tavarez and contributors
# For license information, please see license.txt

import unittest

from .utils import get_repayment_status

from functools import namedtuple

Charge = namedtuple("Charge", ["type", "status"])

class TestRepaymentStatus(unittest.TestCase):
    def test_all_paid(self):
        loan_charges = [
            Charge(type='Capital', status='Paid'),
            Charge(type='Interest', status='Paid'),
            Charge(type='Insurance', status='Paid'),
            Charge(type='GPS', status='Paid'),
        ]
        self.assertEqual(get_repayment_status(loan_charges), 'Paid')

    def test_overdue(self):
        loan_charges = [
            Charge(type='Capital', status='Paid'),
            Charge(type='Interest', status='Overdue'),
            Charge(type='Insurance', status='Paid'),
            Charge(type='GPS', status='Paid'),
        ]
        self.assertEqual(get_repayment_status(loan_charges), 'Overdue')

    def test_partially_paid(self):
        loan_charges = [
            Charge(type='Capital', status='Paid'),
            Charge(type='Interest', status='Partially'),
            Charge(type='Insurance', status='Pending'),
            Charge(type='GPS', status='Pending'),
        ]
        self.assertEqual(get_repayment_status(loan_charges), 'Partially')

    def test_pending(self):
        loan_charges = [
            Charge(type='Capital', status='Paid'),
            Charge(type='Interest', status='Paid'),
            Charge(type='Insurance', status='Pending'),
            Charge(type='GPS', status='Pending'),
        ]
        self.assertEqual(get_repayment_status(loan_charges), 'Pending')

    def test_mixed_statuses(self):
        loan_charges = [
            Charge(type='Capital', status='Paid'),
            Charge(type='Interest', status='Overdue'),
            Charge(type='Insurance', status='Partially'),
            Charge(type='GPS', status='Pending'),
        ]
        self.assertEqual(get_repayment_status(loan_charges), 'Overdue')

    def test_no_loan_charges(self):
        loan_charges = []
        self.assertEqual(get_repayment_status(loan_charges), 'Paid')
