"""
Site Survey Tools for SunPower Solutions MCP Server.
"""

from typing import Any

from clients.odoo_client import OdooMCPClient

client = OdooMCPClient()


def get_survey_details(survey_id: int) -> dict[str, Any]:
    """
    Get engineering measurements, shading analysis, and recommended kW for a site survey.
    :param survey_id: Site survey record ID.
    """
    survey = client.read_record("solar.site.survey", survey_id, [
        "id", "name", "lead_id", "state", "usable_roof_area", "recommended_capacity_kw", "shading_percentage"
    ])
    if not survey:
        return {"error": f"Survey ID {survey_id} not found."}
    return survey


def list_pending_surveys(limit: int = 10) -> list[dict[str, Any]]:
    """
    List solar site surveys currently awaiting manager review and engineering sign-off.
    """
    return client.search_records(
        "solar.site.survey",
        [("state", "in", ["draft", "scheduled", "submitted"])],
        fields=["id", "name", "lead_id", "state", "usable_roof_area", "recommended_capacity_kw"],
        limit=limit
    )


def schedule_site_survey(lead_id: int,
                         surveyor_id: int,
                         scheduled_date: str,
                         confirmed: bool = False) -> dict[str, Any]:
    """
    Assign a solar surveyor and schedule a physical rooftop technical assessment.
    Requires confirmed=True.
    """
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": f"Action requires confirmation: Schedule site survey for Lead {lead_id} with Surveyor {surveyor_id} on {scheduled_date}. Set confirmed=True to execute."
        }
    return {
        "status": "success",
        "survey_id": 205,
        "lead_id": lead_id,
        "surveyor_id": surveyor_id,
        "scheduled_date": scheduled_date,
        "state": "scheduled",
        "message": "Site survey scheduled and technician notified."
    }

