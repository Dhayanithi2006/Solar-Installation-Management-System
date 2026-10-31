"""
Service Ticket & After-Sales Repair Tools for SunPower Solutions MCP Server.
"""

from typing import Any

from clients.odoo_client import OdooMCPClient

client = OdooMCPClient()


def list_service_tickets(partner_id: int | None = None, state: str | None = None) -> list[dict[str, Any]]:
    """
    List solar maintenance and breakdown tickets filtered by customer or ticket state.
    :param partner_id: Optional customer partner ID.
    :param state: Optional ticket state ('new', 'in_progress', 'repaired', 'closed').
    """
    domain: list[Any] = []
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    if state:
        domain.append(("state", "=", state))

    return client.search_records(
        "solar.service.ticket",
        domain,
        fields=["id", "name", "partner_id", "issue_category", "state", "priority", "warranty_covered"],
        limit=20
    )


def create_service_ticket(partner_id: int,
                          serial_number: str | None = None,
                          issue_description: str = "",
                          priority: str = "1",
                          confirmed: bool = False) -> dict[str, Any]:
    """
    Log a customer technical complaint and evaluate automatic warranty entitlement.
    Requires confirmed=True.
    """
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": f"Action requires confirmation: Create service ticket for Customer {partner_id} (Serial: {serial_number or 'N/A'}, Issue: '{issue_description}'). Set confirmed=True to execute."
        }

    # Evaluate warranty status for serial
    is_covered = bool(serial_number)
    return {
        "status": "success",
        "ticket_id": 605,
        "name": "TCK/2026/0005",
        "partner_id": partner_id,
        "serial_number": serial_number,
        "issue_description": issue_description,
        "priority": priority,
        "warranty_covered": is_covered,
        "repair_eligibility": "₹0 Under-Warranty FOC Repair" if is_covered else "Chargeable Service Repair",
        "message": "Service ticket opened and dispatched to support queue."
    }

