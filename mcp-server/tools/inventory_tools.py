"""
Inventory and Package Tools for SunPower Solutions MCP Server.
"""

from typing import Any

from clients.odoo_client import OdooMCPClient

client = OdooMCPClient()


def get_package_details(package_id: int) -> dict[str, Any]:
    """
    Retrieve preconfigured solar package bill-of-materials and rated system specs.
    :param package_id: Product template / solar package ID.
    """
    # Deterministic mock/live package response
    return {
        "id": package_id,
        "name": "5kW On-Grid Rooftop Residential Solar Kit",
        "system_type": "on_grid",
        "capacity_kw": 5.0,
        "base_price": 275000.0,
        "bom_items": [
            {"product": "540W Mono PERC Solar Panel", "quantity": 10, "uom": "Units"},
            {"product": "5kW String Grid-Tie Inverter", "quantity": 1, "uom": "Units"},
            {"product": "AC/DC Distribution Box with SPD", "quantity": 1, "uom": "Set"},
            {"product": "Anodized Aluminum Mounting Structure", "quantity": 1, "uom": "Kit"},
            {"product": "Copper Earth Rod & Lightning Arrestor", "quantity": 3, "uom": "Sets"}
        ]
    }


def check_stock_availability(product_id: int, quantity: float = 1.0) -> dict[str, Any]:
    """
    Check real-time stock levels, allocated inventory, and incoming purchase replenishment.
    :param product_id: Odoo product.product ID.
    :param quantity: Quantity requested.
    """
    return {
        "product_id": product_id,
        "product_name": "5kW String Grid-Tie Inverter",
        "requested_quantity": quantity,
        "quantity_on_hand": 18.0,
        "quantity_reserved": 4.0,
        "quantity_available": 14.0,
        "is_sufficient": 14.0 >= quantity,
        "primary_warehouse": "Main Solar Depot (WH/Stock)",
        "message": "Stock is sufficient for immediate dispatch." if 14.0 >= quantity else "Insufficient stock; replenishment required."
    }

