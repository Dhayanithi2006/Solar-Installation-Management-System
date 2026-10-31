"""
SunPower Solutions — Solar Installation Management System
Dedicated Enterprise MCP Server (Model Context Protocol).

Exposes 19 high-level business tools for AI assistants:
Read-Only Tools:
 1. search_customers
 2. get_customer_details
 3. get_lead_status
 4. get_survey_details
 5. list_pending_surveys
 6. get_package_details
 7. check_stock_availability
 8. get_installation_details
 9. get_solar_passport
10. get_serial_warranty
11. list_service_tickets
12. get_subsidy_status
13. get_monthly_performance
14. get_installation_profitability

Consequential Action / Write Tools (Protected with Confirmation Gates):
15. create_customer_enquiry
16. schedule_site_survey
17. create_service_ticket
18. assign_technician
19. create_followup_activity
20. update_lead_stage
"""

import logging
import os
import sys
from typing import Any

# Ensure server directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mcp.server.fastmcp import FastMCP

import config

app = FastMCP(config.MCP_SERVER_NAME)

from tools.crm_tools import create_followup_activity, get_lead_status, update_lead_stage
from tools.customer_tools import create_customer_enquiry, get_customer_details, search_customers
from tools.installation_tools import assign_technician, get_installation_details, get_solar_passport
from tools.inventory_tools import check_stock_availability, get_package_details
from tools.reporting_tools import get_installation_profitability, get_monthly_performance, get_subsidy_status
from tools.service_tools import create_service_ticket, list_service_tickets
from tools.survey_tools import get_survey_details, list_pending_surveys, schedule_site_survey
from tools.warranty_tools import get_serial_warranty

# Configure enterprise audit logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] [SunPower-MCP] %(message)s"
)
logger = logging.getLogger("SunPowerMCP")

# Server instance initialized above

# =============================================================================
# Read-Only Enterprise Tools
# =============================================================================

@app.tool()
def tool_search_customers(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search for solar customer records by name, email, or phone number."""
    logger.info("MCP Invocation: search_customers(query='%s', limit=%d)", query, limit)
    return search_customers(query=query, limit=limit)


@app.tool()
def tool_get_customer_details(partner_id: int) -> dict[str, Any]:
    """Retrieve full customer profile and solar installation history."""
    logger.info("MCP Invocation: get_customer_details(partner_id=%d)", partner_id)
    return get_customer_details(partner_id=partner_id)


@app.tool()
def tool_get_lead_status(lead_id: int) -> dict[str, Any]:
    """Retrieve stage, monthly electricity bill, and sales assignment for a CRM lead."""
    logger.info("MCP Invocation: get_lead_status(lead_id=%d)", lead_id)
    return get_lead_status(lead_id=lead_id)


@app.tool()
def tool_get_survey_details(survey_id: int) -> dict[str, Any]:
    """Retrieve rooftop engineering measurements, shading %, and system sizing for a survey."""
    logger.info("MCP Invocation: get_survey_details(survey_id=%d)", survey_id)
    return get_survey_details(survey_id=survey_id)


@app.tool()
def tool_list_pending_surveys(limit: int = 10) -> list[dict[str, Any]]:
    """List site surveys currently awaiting manager review and technical sign-off."""
    logger.info("MCP Invocation: list_pending_surveys(limit=%d)", limit)
    return list_pending_surveys(limit=limit)


@app.tool()
def tool_get_package_details(package_id: int) -> dict[str, Any]:
    """Retrieve preconfigured solar package bill of materials and technical specifications."""
    logger.info("MCP Invocation: get_package_details(package_id=%d)", package_id)
    return get_package_details(package_id=package_id)


@app.tool()
def tool_check_stock_availability(product_id: int, quantity: float = 1.0) -> dict[str, Any]:
    """Check warehouse stock levels and available inventory before dispatch."""
    logger.info("MCP Invocation: check_stock_availability(product_id=%d, quantity=%.2f)", product_id, quantity)
    return check_stock_availability(product_id=product_id, quantity=quantity)


@app.tool()
def tool_get_installation_details(installation_id: int) -> dict[str, Any]:
    """Retrieve installation status, technical measurements, GPS, and customer signature."""
    logger.info("MCP Invocation: get_installation_details(installation_id=%d)", installation_id)
    return get_installation_details(installation_id=installation_id)


@app.tool()
def tool_get_solar_passport(passport_id_or_serial: str) -> dict[str, Any]:
    """
    Retrieve consolidated Digital Solar Passport (DSP) lifecycle history,
    including serialized components, warranty statuses, commissioning measurements, and QR token.
    """
    logger.info("MCP Invocation: get_solar_passport(id_or_serial='%s')", passport_id_or_serial)
    return get_solar_passport(passport_id_or_serial=passport_id_or_serial)


@app.tool()
def tool_get_serial_warranty(serial_number: str) -> dict[str, Any]:
    """Lookup real-time warranty coverage, validity window, and days remaining for a serial barcode."""
    logger.info("MCP Invocation: get_serial_warranty(serial_number='%s')", serial_number)
    return get_serial_warranty(serial_number=serial_number)


@app.tool()
def tool_list_service_tickets(partner_id: int | None = None, state: str | None = None) -> list[dict[str, Any]]:
    """List customer maintenance complaints and warranty repair claims."""
    logger.info("MCP Invocation: list_service_tickets(partner_id=%s, state=%s)", partner_id, state)
    return list_service_tickets(partner_id=partner_id, state=state)


@app.tool()
def tool_get_subsidy_status(subsidy_id: int) -> dict[str, Any]:
    """Retrieve national PM Surya Ghar subsidy claim progress and consumer number."""
    logger.info("MCP Invocation: get_subsidy_status(subsidy_id=%d)", subsidy_id)
    return get_subsidy_status(subsidy_id=subsidy_id)


@app.tool()
def tool_get_monthly_performance(month: int | None = None, year: int | None = None) -> dict[str, Any]:
    """Retrieve consolidated operational KPIs for installations, commissioned kW, and revenue."""
    logger.info("MCP Invocation: get_monthly_performance(month=%s, year=%s)", month, year)
    return get_monthly_performance(month=month, year=year)


@app.tool()
def tool_get_installation_profitability(order_id: int) -> dict[str, Any]:
    """Analyze job-costing profitability: revenue, hardware COGS, labor, and gross profit margin."""
    logger.info("MCP Invocation: get_installation_profitability(order_id=%d)", order_id)
    return get_installation_profitability(order_id=order_id)


# =============================================================================
# Consequential Action / Write Enterprise Tools
# =============================================================================

@app.tool()
def tool_create_customer_enquiry(name: str,
                                 phone: str,
                                 email: str | None = None,
                                 monthly_bill: float | None = None,
                                 roof_type: str | None = "concrete",
                                 sanction_load: float | None = None,
                                 confirmed: bool = False) -> dict[str, Any]:
    """Create a new customer lead from a rooftop enquiry. Requires confirmed=True."""
    logger.info("MCP Action: create_customer_enquiry(name='%s', phone='%s', confirmed=%s)", name, phone, confirmed)
    return create_customer_enquiry(
        name=name, phone=phone, email=email, monthly_bill=monthly_bill,
        roof_type=roof_type, sanction_load=sanction_load, confirmed=confirmed
    )


@app.tool()
def tool_schedule_site_survey(lead_id: int,
                              surveyor_id: int,
                              scheduled_date: str,
                              confirmed: bool = False) -> dict[str, Any]:
    """Schedule a technical site survey and assign a technician. Requires confirmed=True."""
    logger.info("MCP Action: schedule_site_survey(lead=%d, surveyor=%d, date='%s', confirmed=%s)", lead_id, surveyor_id, scheduled_date, confirmed)
    return schedule_site_survey(lead_id=lead_id, surveyor_id=surveyor_id, scheduled_date=scheduled_date, confirmed=confirmed)


@app.tool()
def tool_create_service_ticket(partner_id: int,
                               serial_number: str | None = None,
                               issue_description: str = "",
                               priority: str = "1",
                               confirmed: bool = False) -> dict[str, Any]:
    """Log a solar breakdown complaint with automatic warranty check. Requires confirmed=True."""
    logger.info("MCP Action: create_service_ticket(partner=%d, serial='%s', confirmed=%s)", partner_id, serial_number, confirmed)
    return create_service_ticket(partner_id=partner_id, serial_number=serial_number, issue_description=issue_description, priority=priority, confirmed=confirmed)


@app.tool()
def tool_assign_technician(installation_id: int, technician_id: int, confirmed: bool = False) -> dict[str, Any]:
    """Assign a lead solar installation technician to a project. Requires confirmed=True."""
    logger.info("MCP Action: assign_technician(inst=%d, tech=%d, confirmed=%s)", installation_id, technician_id, confirmed)
    return assign_technician(installation_id=installation_id, technician_id=technician_id, confirmed=confirmed)


@app.tool()
def tool_create_followup_activity(lead_id: int,
                                  activity_type: str,
                                  summary: str,
                                  date_deadline: str,
                                  confirmed: bool = False) -> dict[str, Any]:
    """Schedule a next-action activity on a CRM lead. Requires confirmed=True."""
    logger.info("MCP Action: create_followup_activity(lead=%d, type='%s', confirmed=%s)", lead_id, activity_type, confirmed)
    return create_followup_activity(lead_id=lead_id, activity_type=activity_type, summary=summary, date_deadline=date_deadline, confirmed=confirmed)


@app.tool()
def tool_update_lead_stage(lead_id: int, stage: str, confirmed: bool = False) -> dict[str, Any]:
    """Update CRM lead stage in the sales pipeline. Requires confirmed=True."""
    logger.info("MCP Action: update_lead_stage(lead=%d, stage='%s', confirmed=%s)", lead_id, stage, confirmed)
    return update_lead_stage(lead_id=lead_id, stage=stage, confirmed=confirmed)


if __name__ == "__main__":
    from typing import Literal, cast
    transport = cast(Literal["stdio", "sse", "streamable-http"], config.MCP_TRANSPORT)
    logger.info("Starting SunPower Solutions MCP Server via %s transport...", transport)
    app.run(transport=transport)

