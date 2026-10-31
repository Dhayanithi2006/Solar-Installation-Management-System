# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SolarWarrantyRule(models.Model):
    _name = 'solar.warranty.rule'
    _description = 'Solar Product Warranty Policy'
    _order = 'name'

    name = fields.Char(string='Policy Name', required=True)
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Applicable Product Template'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Specific Product Variant'
    )
    duration_value = fields.Integer(string='Duration Value', required=True, default=2)
    duration_unit = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years'),
    ], string='Duration Unit', default='years', required=True)
    component_type = fields.Selection([
        ('inverter', 'Solar Inverter'),
        ('battery', 'Energy Storage Battery'),
        ('charge_controller', 'Charge Controller'),
        ('panel', 'Solar PV Panel'),
        ('bos', 'Balance of System & Wiring'),
        ('other', 'Other Hardware'),
    ], string='Component Category')
    policy_notes = fields.Text(string='Terms, Conditions & Exclusions')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )


class SolarWarrantyRecord(models.Model):
    _name = 'solar.warranty.record'
    _description = 'Serialized Product Warranty Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'warranty_start desc, id desc'

    name = fields.Char(
        string='Warranty Certificate Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Product Serial / Lot Number',
        required=True,
        tracking=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Equipment Product',
        required=True,
        tracking=True
    )
    component_type = fields.Selection(
        related='product_id.solar_component_type',
        string='Component Category',
        store=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer Owner',
        required=True,
        tracking=True
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string='Source Delivery Dispatch',
        tracking=True
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Source Sales Order',
        tracking=True
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Installed Rooftop Job',
        tracking=True
    )
    rule_id = fields.Many2one(
        'solar.warranty.rule',
        string='Applied Warranty Policy',
        tracking=True
    )
    warranty_start = fields.Date(
        string='Warranty Start Date',
        required=True,
        tracking=True,
        help='Effective delivery completion date when the warranty clock begins.'
    )
    warranty_end = fields.Date(
        string='Warranty Expiry Date',
        required=True,
        compute='_compute_warranty_end',
        store=True,
        readonly=False,
        tracking=True
    )
    days_remaining = fields.Integer(
        string='Days Remaining',
        compute='_compute_days_remaining',
        store=True
    )
    is_valid = fields.Boolean(
        string='Is Currently Under Warranty',
        compute='_compute_days_remaining',
        store=True
    )
    state = fields.Selection([
        ('active', 'Active (Under Warranty)'),
        ('expired', 'Warranty Expired'),
        ('void', 'Void / Cancelled'),
    ], string='Status', default='active', compute='_compute_state', store=True, tracking=True)

    service_ticket_ids = fields.One2many(
        'solar.service.ticket',
        'warranty_id',
        string='Service & Breakdown Claims'
    )
    ticket_count = fields.Integer(
        string='Claims Count',
        compute='_compute_ticket_count'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.depends('warranty_start', 'rule_id')
    def _compute_warranty_end(self):
        for record in self:
            if record.warranty_start and record.rule_id:
                val = record.rule_id.duration_value or 2
                unit = record.rule_id.duration_unit or 'years'
                delta = relativedelta(years=val) if unit == 'years' else relativedelta(months=val) if unit == 'months' else relativedelta(days=val)
                record.warranty_end = record.warranty_start + delta
            elif not record.warranty_end:
                record.warranty_end = record.warranty_start

    @api.depends('warranty_end', 'state')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for record in self:
            if record.warranty_end:
                diff = (record.warranty_end - today).days
                record.days_remaining = max(diff, 0)
                record.is_valid = (diff >= 0 and record.state == 'active')
            else:
                record.days_remaining = 0
                record.is_valid = False

    @api.depends('warranty_end')
    def _compute_state(self):
        today = fields.Date.today()
        for record in self:
            if record.state == 'void':
                continue
            if record.warranty_end and record.warranty_end < today:
                record.state = 'expired'
            else:
                record.state = 'active'

    @api.depends('service_ticket_ids')
    def _compute_ticket_count(self):
        for record in self:
            record.ticket_count = len(record.service_ticket_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.warranty.record') or _('New')
        return super().create(vals_list)

    def action_void_warranty(self):
        """Manager voids warranty certificate due to customer damage or unauthorized alteration."""
        self.ensure_one()
        self.write({'state': 'void'})
        self.message_post(body=_("Warranty certificate voided by %s.") % self.env.user.name)

    def action_reactivate_warranty(self):
        """Re-activate voided warranty if dispute resolved."""
        self.ensure_one()
        self.write({'state': 'active'})
        self.message_post(body=_("Warranty certificate re-activated by %s.") % self.env.user.name)

    def action_create_service_ticket(self):
        """Action button to raise a service breakdown claim directly from this warranty."""
        self.ensure_one()
        ticket_vals = {
            'partner_id': self.partner_id.id,
            'lot_id': self.lot_id.id,
            'product_id': self.product_id.id,
            'warranty_id': self.id,
            'company_id': self.company_id.id,
        }
        ticket = self.env['solar.service.ticket'].create(ticket_vals)
        return {
            'name': _('Customer Service Claim'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.service.ticket',
            'res_id': ticket.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_service_tickets(self):
        """Smart button action to view service claims linked to this warranty."""
        self.ensure_one()
        return {
            'name': _('Service Claims for Certificate %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.service.ticket',
            'view_mode': 'list,form',
            'domain': [('warranty_id', '=', self.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_lot_id': self.lot_id.id,
                'default_product_id': self.product_id.id,
                'default_warranty_id': self.id,
            },
        }

    @api.model
    def _cron_check_warranty_expiration(self):
        """Nightly scheduled action to transition elapsed warranty records from active to expired."""
        today = fields.Date.today()
        expired_warranties = self.search([
            ('state', '=', 'active'),
            ('warranty_end', '<', today),
        ])
        if expired_warranties:
            expired_warranties.write({'state': 'expired'})
            _logger = self.env['ir.logging']
            self.env.cr.commit()
        return True

