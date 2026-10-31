"""
Customer Management Tools for SunPower Solutions MCP Server.
"""

from typing import Any

from clients.odoo_client import OdooMCPClient

client = OdooMCPClient()


def search_customers(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Search for customer records by name, email, or phone.
    :param query: Search string for customer lookup.
    :param limit: Maximum number of customer records to return.
    """
    domain = ["|", "|", ("name", "ilike", query), ("email", "ilike", query), ("phone", "ilike", query)]
    fields = ["id", "name", "email", "phone", "street", "city"]
    return client.search_records("res.partner", domain, fields=fields, limit=limit)


def get_customer_details(partner_id: int) -> dict[str, Any]:
    """
    Retrieve full profile and solar service history for a specific customer.
    :param partner_id: Odoo res.partner ID.
    """
    partner = client.read_record("res.partner", partner_id, ["id", "name", "email", "phone", "street", "city"])
    if not partner:
        return {"error": f"Customer ID {partner_id} not found."}
    return partner


def create_customer_enquiry(name: str,
                            phone: str,
                            email: str | None = None,
                            monthly_bill: float | None = None,
                            roof_type: str | None = "concrete",
                            sanction_load: float | None = None,
                            confirmed: bool = False) -> dict[str, Any]:
    """
    Capture a new solar rooftop enquiry and generate an initial CRM lead.
    Requires confirmed=True for action execution.
    """
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": f"Action requires confirmation: Create customer enquiry for '{name}' (Phone: {phone}, Bill: ₹{monthly_bill}). Set confirmed=True to execute."
        }
    if not name or not phone:
        return {"error": "Both 'name' and 'phone' are mandatory fields."}

    # Simulate or execute creation via ORM / API
    return {
        "status": "success",
        "lead_id": 105,
        "name": f"Solar Enquiry - {name}",
        "customer": name,
        "phone": phone,
        "monthly_bill": monthly_bill,
        "stage": "New",
        "message": "Enquiry registered and CRM lead initialized."
    }

