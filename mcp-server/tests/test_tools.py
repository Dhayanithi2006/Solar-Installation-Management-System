"""
Unit Tests for all 19 SunPower Solutions MCP Tools.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.crm_tools import create_followup_activity, get_lead_status, update_lead_stage
from tools.customer_tools import create_customer_enquiry, get_customer_details, search_customers
from tools.installation_tools import assign_technician, get_installation_details, get_solar_passport
from tools.inventory_tools import check_stock_availability, get_package_details
from tools.reporting_tools import get_installation_profitability, get_monthly_performance, get_subsidy_status
from tools.service_tools import create_service_ticket, list_service_tickets
from tools.survey_tools import get_survey_details, list_pending_surveys, schedule_site_survey
from tools.warranty_tools import get_serial_warranty


class TestMCPTools(unittest.TestCase):

    # 1. search_customers
    def test_search_customers(self):
        res = search_customers("Aditi")
        self.assertIsInstance(res, list)
        self.assertTrue(len(res) > 0)
        self.assertIn("Aditi", res[0]["name"])

    # 2. get_customer_details
    def test_get_customer_details(self):
        res = get_customer_details(1)
        self.assertIn("id", res)
        self.assertEqual(res["id"], 1)

    # 3. get_lead_status
    def test_get_lead_status(self):
        res = get_lead_status(101)
        self.assertEqual(res["id"], 101)
        self.assertIn("partner_id", res)

    # 4. get_survey_details
    def test_get_survey_details(self):
        res = get_survey_details(201)
        self.assertEqual(res["id"], 201)
        self.assertEqual(res["state"], "approved")

    # 5. list_pending_surveys
    def test_list_pending_surveys(self):
        res = list_pending_surveys()
        self.assertIsInstance(res, list)

    # 6. get_package_details
    def test_get_package_details(self):
        res = get_package_details(1)
        self.assertEqual(res["capacity_kw"], 5.0)
        self.assertTrue(len(res["bom_items"]) >= 4)

    # 7. check_stock_availability
    def test_check_stock_availability(self):
        res = check_stock_availability(10, 2.0)
        self.assertTrue(res["is_sufficient"])
        self.assertEqual(res["requested_quantity"], 2.0)

    # 8. get_installation_details
    def test_get_installation_details(self):
        res = get_installation_details(301)
        self.assertEqual(res["id"], 301)
        self.assertEqual(res["state"], "completed")

    # 9. get_solar_passport
    def test_get_solar_passport(self):
        res = get_solar_passport("DSP/2026/00001")
        self.assertEqual(res["name"], "DSP/2026/00001")
        self.assertIn("registered_components", res)
        self.assertIn("commissioning_metrics", res)

    # 10. get_serial_warranty
    def test_get_serial_warranty(self):
        res = get_serial_warranty("INV-SUN-2026-008")
        self.assertEqual(res["serial_number"], "INV-SUN-2026-008")
        self.assertTrue(res["is_valid"])
        self.assertTrue(res["is_eligible_for_zero_rupee_repair"])

    # 11. list_service_tickets
    def test_list_service_tickets(self):
        res = list_service_tickets(partner_id=1)
        self.assertIsInstance(res, list)

    # 12. get_subsidy_status
    def test_get_subsidy_status(self):
        res = get_subsidy_status(701)
        self.assertEqual(res["id"], 701)
        self.assertEqual(res["state"], "approved")

    # 13. get_monthly_performance
    def test_get_monthly_performance(self):
        res = get_monthly_performance(10, 2026)
        self.assertEqual(res["installations_completed"], 12)
        self.assertIn("total_revenue_invoiced_inr", res)

    # 14. get_installation_profitability
    def test_get_installation_profitability(self):
        res = get_installation_profitability(42)
        self.assertEqual(res["order_id"], 42)
        self.assertTrue(res["gross_margin_percent"] > 20.0)

    # Action Tools with confirmed=True
    def test_create_customer_enquiry(self):
        res = create_customer_enquiry("Sunita Rao", "+91 99887 76655", monthly_bill=6500.0, confirmed=True)
        self.assertEqual(res["status"], "success")
        self.assertIn("lead_id", res)

    def test_schedule_site_survey(self):
        res = schedule_site_survey(101, 5, "2026-11-05", confirmed=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["state"], "scheduled")

    def test_create_service_ticket(self):
        res = create_service_ticket(1, "INV-SUN-2026-008", "Inverter red error light", confirmed=True)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["warranty_covered"])

    def test_assign_technician(self):
        res = assign_technician(301, 7, confirmed=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["lead_technician_id"], 7)

    def test_create_followup_activity(self):
        res = create_followup_activity(101, "call", "Discuss subsidy documentation", "2026-11-03", confirmed=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["activity_type"], "call")

    def test_update_lead_stage(self):
        res = update_lead_stage(101, "Quotation Sent", confirmed=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["new_stage"], "Quotation Sent")


if __name__ == '__main__':
    unittest.main()

