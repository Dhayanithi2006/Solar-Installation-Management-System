# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_solar_component = fields.Boolean(
        string='Is Solar Component',
        default=False,
        help='Check if this product is used in solar rooftop installations or package BoMs.'
    )
    solar_component_type = fields.Selection([
        ('panel', 'Solar PV Panel'),
        ('inverter', 'Inverter (On-Grid / Hybrid)'),
        ('battery', 'Energy Storage Battery'),
        ('charge_controller', 'Solar Charge Controller'),
        ('structure', 'Mounting Stands & Structure'),
        ('wiring', 'DC/AC Cables & Wiring'),
        ('safety', 'Wiring Boxes & Safety Earthing'),
        ('service', 'Installation & Testing Service'),
        ('accessory', 'Other Consumables / Accessories'),
    ], string='Solar Component Type', tracking=True)

    solar_capacity_watts = fields.Float(
        string='Rated Capacity (Watts / VA)',
        help='Nominal wattage rating for panels, inverters, and battery capacities.'
    )
    is_serial_required = fields.Boolean(
        string='Requires Serial Scan Before Dispatch',
        compute='_compute_is_serial_required',
        store=True,
        help='Flag indicating whether unique serial number verification is mandatory on warehouse picking.'
    )
    default_warranty_rule_id = fields.Many2one(
        'solar.warranty.rule',
        string='Default Warranty Policy',
        help='Standard warranty terms applied to this product upon delivery completion.'
    )

    @api.depends('solar_component_type', 'tracking')
    def _compute_is_serial_required(self):
        for record in self:
            if record.solar_component_type in ('inverter', 'battery', 'charge_controller') or record.tracking == 'serial':
                record.is_serial_required = True
            else:
                record.is_serial_required = False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def is_serial_verification_required(self):
        """Helper method called by picking dispatch verification."""
        self.ensure_one()
        return self.is_serial_required or self.tracking == 'serial'

