"""
Unit Tests for Odoo MCP Client.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from clients.odoo_client import OdooMCPClient


class TestOdooMCPClient(unittest.TestCase):

    def setUp(self):
        self.client = OdooMCPClient(use_mock=True)

    def test_mock_search_customers(self):
        records = self.client.search_records("res.partner", [("name", "ilike", "Aditi")])
        self.assertTrue(len(records) > 0)
        self.assertEqual(records[0]["name"], "Aditi Sharma")

    def test_mock_read_record_found(self):
        rec = self.client.read_record("res.partner", 1)
        self.assertIsNotNone(rec)
        assert rec is not None
        self.assertEqual(rec["id"], 1)

    def test_mock_read_record_not_found(self):
        rec = self.client.read_record("res.partner", 99999)
        self.assertIsNone(rec)

    def test_mock_search_passports(self):
        records = self.client.search_records("solar.passport", [("name", "=", "DSP/2026/00001")])
        self.assertTrue(len(records) > 0)
        self.assertEqual(records[0]["name"], "DSP/2026/00001")


if __name__ == '__main__':
    unittest.main()

