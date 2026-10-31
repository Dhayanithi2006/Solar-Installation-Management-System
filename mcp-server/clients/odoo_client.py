"""
SunPower Solutions — High-Level Odoo ERP Client for MCP Server.
Provides resilient connectivity to Odoo via:
1. Live Odoo MCP Server endpoint (Bearer token JSON-RPC)
2. Direct REST API endpoints (/api/solar/v1)
3. Deterministic Mock Fallback for hermetic unit testing and offline demo execution.
"""

import json
import logging
import ssl
import urllib.error
import urllib.request
from typing import Any

import config

logger = logging.getLogger(__name__)


class OdooMCPClient:
    """Enterprise client managing communication between MCP Tools and Odoo ERP."""

    def __init__(self,
                 mcp_url: str | None = None,
                 auth_token: str | None = None,
                 use_mock: bool = config.USE_MOCK_FALLBACK):
        self.mcp_url = mcp_url or config.ODOO_MCP_URL
        self.auth_token = auth_token or config.ODOO_MCP_TOKEN
        self.use_mock = use_mock
        self._ctx = ssl.create_default_context()
        self._request_id = 1

    def _call_live_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke a low-level tool on the live Odoo MCP Server via JSON-RPC."""
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        req = urllib.request.Request(
            self.mcp_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, context=self._ctx, timeout=config.TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "error" in data:
                    raise RuntimeError(f"Odoo MCP Error: {data['error']}")
                return data.get("result", {})
        except Exception as e:
            logger.warning(f"Live Odoo MCP call failed ({e}). Falling back to mock if enabled.")
            if self.use_mock:
                return self._mock_dispatch(tool_name, arguments)
            raise

    def search_records(self, model: str, domain: list[Any], fields: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Search and read records from an Odoo model."""
        if self.use_mock:
            return self._mock_search(model, domain, fields, limit)
        try:
            res = self._call_live_mcp_tool("ai_tool_search", {
                "model": model,
                "domain": domain,
                "fields": fields or ["id", "display_name"],
                "limit": limit
            })
            return res.get("records", [])
        except Exception:
            if self.use_mock:
                return self._mock_search(model, domain, fields, limit)
            raise

    def read_record(self, model: str, res_id: int, fields: list[str] | None = None) -> dict[str, Any] | None:
        """Read a single record by ID."""
        records = self.search_records(model, [("id", "=", res_id)], fields=fields, limit=1)
        return records[0] if records else None

    # =========================================================================
    # Mock Data Dispatcher for Hermetic Validation
    # =========================================================================
    def _mock_dispatch(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch mock operations for automated test suites."""
        return {"records": self._mock_search(arguments.get("model", ""), arguments.get("domain", []), limit=10)}

    def _mock_search(self, model: str, domain: list[Any], fields: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """In-memory mock store representing verified project data."""
        records = []
        if model == "res.partner":
            records = [
                {"id": 1, "name": "Aditi Sharma", "email": "aditi.sharma@example.com", "phone": "+91 98765 43210", "street": "42 Green Enclave", "city": "Jaipur"},
                {"id": 2, "name": "Rajesh Verma", "email": "rajesh.verma@example.com", "phone": "+91 98111 22334", "street": "104 Sun City", "city": "Jodhpur"},
            ]
        elif model == "crm.lead":
            records = [
                {"id": 101, "name": "Aditi Sharma 5kW Rooftop", "partner_id": [1, "Aditi Sharma"], "monthly_bill": 4500.0, "stage_id": [1, "New"], "user_id": [2, "Sales Rep"]},
                {"id": 102, "name": "Rajesh Verma 10kW Commercial", "partner_id": [2, "Rajesh Verma"], "monthly_bill": 12000.0, "stage_id": [2, "Survey Scheduled"], "user_id": [2, "Sales Rep"]},
            ]
        elif model == "solar.site.survey":
            records = [
                {"id": 201, "name": "SURV/2026/0001", "lead_id": [101, "Aditi Sharma 5kW"], "state": "approved", "usable_roof_area": 45.0, "recommended_capacity_kw": 5.0, "shading_percentage": 2.5},
                {"id": 202, "name": "SURV/2026/0002", "lead_id": [102, "Rajesh Verma 10kW"], "state": "submitted", "usable_roof_area": 95.0, "recommended_capacity_kw": 10.0, "shading_percentage": 4.0},
            ]
        elif model == "solar.installation":
            records = [
                {"id": 301, "name": "INST/2026/0001", "partner_id": [1, "Aditi Sharma"], "state": "completed", "installed_capacity_kw": 5.0, "test_generation_kw": 4.95, "customer_signed_by": "Aditi Sharma"},
                {"id": 302, "name": "INST/2026/0002", "partner_id": [2, "Rajesh Verma"], "state": "scheduled", "installed_capacity_kw": 10.0, "test_generation_kw": 0.0, "customer_signed_by": False},
            ]
        elif model == "solar.passport":
            records = [
                {
                    "id": 401,
                    "name": "DSP/2026/00001",
                    "partner_id": [1, "Aditi Sharma"],
                    "installation_id": [301, "INST/2026/0001"],
                    "installed_capacity_kw": 5.0,
                    "system_type": "on_grid",
                    "commissioning_date": "2026-10-31",
                    "state": "active",
                    "verification_token": "a1b2c3d4-e5f6-7890",
                    "verification_url": "https://solar-installation-management-system.odoo.com/passport/verify/a1b2c3d4-e5f6-7890"
                }
            ]
        elif model == "solar.warranty.record":
            records = [
                {"id": 501, "name": "WAR/2026/0001", "serial_number": "INV-SUN-2026-008", "state": "active", "is_valid": True, "warranty_end": "2031-10-31", "days_remaining": 1825},
                {"id": 502, "name": "WAR/2026/0002", "serial_number": "PAN-MONO-2026-042", "state": "active", "is_valid": True, "warranty_end": "2051-10-31", "days_remaining": 9125},
            ]
        elif model == "solar.service.ticket":
            records = [
                {"id": 601, "name": "TCK/2026/0001", "partner_id": [1, "Aditi Sharma"], "issue_category": "inverter_fault", "state": "new", "priority": "2", "warranty_covered": True},
            ]
        elif model == "solar.subsidy.case":
            records = [
                {"id": 701, "name": "SUB/2026/0001", "partner_id": [1, "Aditi Sharma"], "capacity_kw": 5.0, "calculated_cfa_subsidy": 78000.0, "state": "approved", "discom_consumer_no": "DISCOM-DEL-9876"},
            ]

        # Domain filtering: support OR prefixes and field matching
        clauses = [c for c in domain if isinstance(c, (tuple, list)) and len(c) == 3]
        has_or = "|" in domain

        if has_or and clauses:
            filtered = []
            for r in records:
                matched = False
                for field, op, val in clauses:
                    if op == "=" and r.get(field) == val or op == "ilike" and val.lower() in str(r.get(field, "")).lower():
                        matched = True
                        break
                if matched:
                    filtered.append(r)
            records = filtered
        else:
            for field, op, val in clauses:
                if op == "=" and field == "id":
                    records = [r for r in records if r.get("id") == val]
                elif op == "=" and field in ("name", "serial_number"):
                    records = [r for r in records if r.get(field) == val]
                elif op == "ilike" and field in ("name", "email", "phone"):
                    records = [r for r in records if val.lower() in str(r.get(field, "")).lower()]

        return records[:limit]
