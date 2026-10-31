"""
CRM & Sales Pipeline Tools for SunPower Solutions MCP Server.
"""

from typing import Any

from clients.odoo_client import OdooMCPClient

client = OdooMCPClient()


def get_lead_status(lead_id: int) -> dict[str, Any]:
    """
    Get current pipeline stage, expected revenue, and assigned sales rep for a CRM lead.
    :param lead_id: CRM lead ID.
    """
    lead = client.read_record("crm.lead", lead_id, ["id", "name", "partner_id", "monthly_bill", "stage_id", "user_id"])
    if not lead:
        return {"error": f"Lead ID {lead_id} not found."}
    return lead


def create_followup_activity(lead_id: int,
                             activity_type: str,
                             summary: str,
                             date_deadline: str,
                             confirmed: bool = False) -> dict[str, Any]:
    """
    Schedule a next-action follow-up activity on a solar CRM opportunity.
    Requires confirmed=True.
    """
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": f"Action requires confirmation: Schedule '{activity_type}' for Lead {lead_id} by {date_deadline} ('{summary}'). Set confirmed=True to execute."
        }
    return {
        "status": "success",
        "activity_id": 8801,
        "lead_id": lead_id,
        "activity_type": activity_type,
        "summary": summary,
        "deadline": date_deadline,
        "message": "Follow-up activity successfully scheduled."
    }


def update_lead_stage(lead_id: int, stage: str, confirmed: bool = False) -> dict[str, Any]:
    """
    Advance or change the lifecycle stage of a solar CRM lead.
    Requires confirmed=True.
    """
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": f"Action requires confirmation: Advance Lead {lead_id} to stage '{stage}'. Set confirmed=True to execute."
        }
    return {
        "status": "success",
        "lead_id": lead_id,
        "new_stage": stage,
        "message": f"Lead {lead_id} transitioned to stage '{stage}'."
    }

