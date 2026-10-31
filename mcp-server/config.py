"""
SunPower Solutions — Solar Installation Management System
MCP Server Configuration Settings.
Loads connection parameters, auth tokens, timeout, log levels, and security constraints.
"""

import os

# Odoo ERP Backend Configuration
ODOO_URL = os.environ.get("ODOO_URL", "https://solar-installation-management-system.odoo.com")
ODOO_DATABASE = os.environ.get("ODOO_DATABASE", "solar_db")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "")
ODOO_API_KEY = os.environ.get("ODOO_API_KEY", "")

# Dedicated Live MCP Server Endpoint & Bearer Token
ODOO_MCP_URL = os.environ.get("ODOO_MCP_URL", "https://solar-installation-management-system.odoo.com/mcp")
ODOO_MCP_TOKEN = os.environ.get("ODOO_MCP_TOKEN", "e1f3185c8696cdb7ad0b5594c1b00a76e6b1dbe3_oak")

# Server Settings
MCP_SERVER_NAME = "SunPowerSolutions-MCP"
MCP_SERVER_VERSION = "1.0.0"
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", "30"))

# Mock/Hermetic Mode for Offline Testing & Demos
USE_MOCK_FALLBACK = os.environ.get("USE_MOCK_FALLBACK", "true").lower() in ("true", "1", "yes")

# Safety & Confirmation Gates
# Consequential actions requiring explicit confirmation payload parameter
CONSEQUENTIAL_ACTIONS: set[str] = {
    "create_customer_enquiry",
    "schedule_site_survey",
    "create_service_ticket",
    "assign_technician",
    "update_lead_stage"
}

