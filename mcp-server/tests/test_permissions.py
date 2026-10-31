"""
Safety & Permission Gate Tests for SunPower Solutions MCP Server.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.crm_tools import create_followup_activity, update_lead_stage
from tools.customer_tools import create_customer_enquiry
from tools.installation_tools import assign_technician
from tools.service_tools import create_service_ticket
from tools.survey_tools import schedule_site_survey


class TestMCPPermissionsAndSafety(unittest.TestCase):

    def test_create_enquiry_requires_confirmation(self):
        res = create_customer_enquiry("Rohan", "+91 91234 56789", confirmed=False)
        self.assertEqual(res["status"], "confirmation_required")
        self.assertIn("requires confirmation", res["message"])

    def test_create_enquiry_missing_fields(self):
        res = create_customer_enquiry("", "", confirmed=True)
        self.assertIn("error", res)

    def test_schedule_survey_requires_confirmation(self):
        res = schedule_site_survey(101, 5, "2026-11-05", confirmed=False)
        self.assertEqual(res["status"], "confirmation_required")

    def test_create_ticket_requires_confirmation(self):
        res = create_service_ticket(1, "INV-001", "Overheating", confirmed=False)
        self.assertEqual(res["status"], "confirmation_required")

    def test_assign_technician_requires_confirmation(self):
        res = assign_technician(301, 7, confirmed=False)
        self.assertEqual(res["status"], "confirmation_required")

    def test_create_followup_requires_confirmation(self):
        res = create_followup_activity(101, "email", "Send catalog", "2026-11-04", confirmed=False)
        self.assertEqual(res["status"], "confirmation_required")

    def test_update_stage_requires_confirmation(self):
        res = update_lead_stage(101, "Won", confirmed=False)
        self.assertEqual(res["status"], "confirmation_required")


if __name__ == '__main__':
    unittest.main()
