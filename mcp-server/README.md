# SunPower Solutions — Dedicated MCP Server

Model Context Protocol (MCP) server integration for the **SunPower Solutions — Solar Installation Management System**.

## Capabilities

Exposes 19 high-level business tools across solar operations:
1. `search_customers`: Full-text customer contact lookup.
2. `get_customer_details`: Comprehensive customer profile & installation records.
3. `get_lead_status`: CRM stage, electricity bill, and lead owner.
4. `get_survey_details`: Rooftop measurements, shading analysis, and system sizing.
5. `list_pending_surveys`: Unapproved site surveys awaiting review.
6. `get_package_details`: Solar package BoM breakdown and electrical parameters.
7. `check_stock_availability`: Real-time warehouse balance and allocation checks.
8. `get_installation_details`: Electrical commissioning test results, GPS, and sign-offs.
9. `get_solar_passport`: Consolidated Digital Solar Passport (DSP) lifecycle history, serialized component registry, warranty status, and QR verification.
10. `get_serial_warranty`: Real-time warranty coverage, validity window, and policy details.
11. `list_service_tickets`: Active solar breakdown complaints and claims.
12. `get_subsidy_status`: National PM Surya Ghar portal progress and CFA subsidies.
13. `get_monthly_performance`: Monthly operational KPIs and commissioning metrics.
14. `get_installation_profitability`: Job costing, hardware COGS, labor, and gross profit margin.

### Consequential Action Tools (Protected with Confirmation Gates)
15. `create_customer_enquiry`: Captures new rooftop enquiries.
16. `schedule_site_survey`: Dispatches surveyor with confirmed appointment.
17. `create_service_ticket`: Logs breakdown complaints with instant ₹0 vs chargeable warranty calculation.
18. `assign_technician`: Assigns lead installation technician.
19. `create_followup_activity`: Schedules sales follow-ups and deadline reminders.
20. `update_lead_stage`: Advances CRM opportunity stages.

## Configuration

Copy `.env.example` to `.env`:
```bash
ODOO_URL=https://solar-installation-management-system.odoo.com
ODOO_DATABASE=solar_db
ODOO_USERNAME=mcp_service_user
ODOO_MCP_URL=https://solar-installation-management-system.odoo.com/mcp
ODOO_MCP_TOKEN=e1f3185c8696cdb7ad0b5594c1b00a76e6b1dbe3_oak
MCP_TRANSPORT=stdio
LOG_LEVEL=INFO
USE_MOCK_FALLBACK=true
```

## Running the Server

Run via stdio transport:
```bash
python mcp-server/server.py
```

## Running Tests

```bash
python -m unittest discover -s mcp-server/tests -v
```

