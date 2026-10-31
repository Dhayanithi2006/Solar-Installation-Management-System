# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer Owner',
        tracking=True,
        help='Customer at whose site this serialized solar equipment is deployed.'
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Deployed Installation',
        tracking=True,
        help='Rooftop installation project where this unit is installed.'
    )
    is_solar_equipment = fields.Boolean(
        string='Is Solar Equipment',
        compute='_compute_is_solar_equipment',
        store=True
    )
    solar_component_type = fields.Selection(
        related='product_id.solar_component_type',
        string='Solar Equipment Type',
        store=True,
        readonly=True
    )
    warranty_record_ids = fields.One2many(
        'solar.warranty.record',
        'lot_id',
        string='Warranty Records'
    )
    warranty_record_id = fields.Many2one(
        'solar.warranty.record',
        string='Active Warranty Record',
        compute='_compute_active_warranty',
        store=True
    )
    warranty_status = fields.Selection([
        ('no_warranty', 'No Active Warranty'),
        ('active', 'Under Active Warranty'),
        ('expired', 'Warranty Expired'),
        ('void', 'Void'),
    ], string='Warranty Status', compute='_compute_active_warranty', store=True, tracking=True)

    @api.depends('product_id.is_solar_component')
    def _compute_is_solar_equipment(self):
        for lot in self:
            lot.is_solar_equipment = bool(lot.product_id.is_solar_component)

    @api.depends('warranty_record_ids.state', 'warranty_record_ids.warranty_end')
    def _compute_active_warranty(self):
        today = fields.Date.today()
        for lot in self:
            active_warranties = lot.warranty_record_ids.filtered(lambda w: w.state == 'active')
            if active_warranties:
                lot.warranty_record_id = active_warranties[0].id
                lot.warranty_status = 'active'
            elif any(w.state == 'expired' or (w.warranty_end and w.warranty_end < today) for w in lot.warranty_record_ids):
                lot.warranty_record_id = lot.warranty_record_ids[0].id if lot.warranty_record_ids else False
                lot.warranty_status = 'expired'
            else:
                lot.warranty_record_id = False
                lot.warranty_status = 'no_warranty'

    def action_view_warranty(self):
        """Smart button action to view warranty records linked to this serial number."""
        self.ensure_one()
        return {
            'name': _('Warranty Records for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.warranty.record',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'default_product_id': self.product_id.id,
                'default_partner_id': self.customer_id.id if self.customer_id else False,
            },
        }

    def action_view_service_tickets(self):
        """Smart button action to view service tickets for this equipment."""
        self.ensure_one()
        return {
            'name': _('Service Tickets for Serial %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.service.ticket',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'default_partner_id': self.customer_id.id if self.customer_id else False,
            },
        }

