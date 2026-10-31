# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    ticket_id = fields.Many2one(
        'solar.service.ticket',
        string='Source Service Ticket',
        tracking=True,
        copy=False,
        help='Solar customer service breakdown claim triggering this repair operation.'
    )
    is_solar_repair = fields.Boolean(
        string='Is Solar Equipment Repair',
        compute='_compute_is_solar_repair',
        store=True,
        tracking=True
    )
    warranty_id = fields.Many2one(
        'solar.warranty.record',
        string='Applied Warranty Certificate',
        tracking=True
    )
    warranty_coverage_status = fields.Selection([
        ('covered', 'Under Active Warranty (₹0 Covered Repair)'),
        ('out_of_warranty', 'Out of Warranty (Chargeable Customer Billing)'),
        ('void', 'Warranty Voided (Chargeable Customer Billing)'),
    ], string='Warranty Decision', default='covered', tracking=True)

    warranty_notes = fields.Text(
        string='Warranty Billing Notes',
        tracking=True,
        help='Audit documentation detailing whether replacement parts and technician labor are ₹0 covered or invoiced.'
    )

    is_covered_repair = fields.Boolean(
        string='Zero Cost Warranty Repair',
        compute='_compute_is_covered_repair',
        store=True
    )

    @api.depends('ticket_id', 'product_id', 'lot_id')
    def _compute_is_solar_repair(self):
        for repair in self:
            repair.is_solar_repair = bool(
                repair.ticket_id or
                (repair.product_id and repair.product_id.is_solar_component) or
                (repair.lot_id and repair.lot_id.is_solar_equipment)
            )

    @api.depends('warranty_coverage_status')
    def _compute_is_covered_repair(self):
        for repair in self:
            repair.is_covered_repair = (repair.warranty_coverage_status == 'covered')

    def action_validate(self):
        """When repair is completed, synchronize resolution back to the source service ticket."""
        res = super().action_validate() if hasattr(super(), 'action_validate') else True
        for repair in self:
            if repair.ticket_id:
                repair.ticket_id.message_post(body=_(
                    "Repair Order %s has been executed. Repaired/replaced equipment is ready for customer confirmation."
                ) % repair.name)
        return res

