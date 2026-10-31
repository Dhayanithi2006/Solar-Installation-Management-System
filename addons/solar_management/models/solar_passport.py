# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SolarPassport(models.Model):
    """
    Digital Solar Passport (DSP).
    Unified lifecycle registry consolidating customer, project, installed serialized
    components, real-time warranty timelines, installation evidence, and service history.
    """
    _name = 'solar.passport'
    _description = 'Digital Solar Passport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Digital Passport ID',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer Owner',
        required=True,
        tracking=True
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Installation Job',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        related='installation_id.sale_order_id',
        store=True,
        readonly=True
    )
    survey_id = fields.Many2one(
        'solar.site.survey',
        string='Approved Site Survey',
        related='installation_id.survey_id',
        store=True,
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Operating Company',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )

    # Technical System Attributes
    installed_capacity_kw = fields.Float(
        string='System Capacity (kW)',
        related='installation_id.installed_capacity_kw',
        store=True,
        readonly=True
    )
    system_type = fields.Selection([
        ('on_grid', 'On-Grid Rooftop'),
        ('off_grid', 'Off-Grid with Battery Storage'),
        ('hybrid', 'Hybrid Grid-Interactive with Backup'),
    ], string='System Architecture', default='on_grid', tracking=True)

    commissioning_date = fields.Date(
        string='Commissioning Date',
        default=fields.Date.context_today,
        tracking=True
    )
    lead_technician_id = fields.Many2one(
        'res.users',
        string='Lead Commissioning Technician',
        related='installation_id.lead_technician_id',
        store=True,
        readonly=True
    )

    # Commissioning Evidence & Power Measurements
    gps_latitude = fields.Float(
        string='Commissioning Latitude',
        related='installation_id.gps_latitude',
        store=True,
        readonly=True
    )
    gps_longitude = fields.Float(
        string='Commissioning Longitude',
        related='installation_id.gps_longitude',
        store=True,
        readonly=True
    )
    test_dc_voltage = fields.Float(
        string='DC String Voltage (V)',
        related='installation_id.test_dc_voltage',
        store=True,
        readonly=True
    )
    test_ac_voltage = fields.Float(
        string='AC Grid Voltage (V)',
        related='installation_id.test_ac_voltage',
        store=True,
        readonly=True
    )
    test_generation_kw = fields.Float(
        string='Peak Commissioned Generation (kW)',
        related='installation_id.test_generation_kw',
        store=True,
        readonly=True
    )
    customer_signed_by = fields.Char(
        string='Accepted By Customer',
        related='installation_id.customer_signed_by',
        store=True,
        readonly=True
    )
    customer_signed_date = fields.Datetime(
        string='Signed On Date',
        related='installation_id.customer_signed_date',
        store=True,
        readonly=True
    )

    # Component Registry & Lifecycle Linkages
    component_ids = fields.One2many(
        'solar.passport.component',
        'passport_id',
        string='Installed Component Registry'
    )
    component_count = fields.Integer(
        string='Registered Components',
        compute='_compute_counts'
    )
    service_ticket_ids = fields.Many2many(
        'solar.service.ticket',
        string='Service & Breakdown Claims',
        compute='_compute_service_history'
    )
    service_ticket_count = fields.Integer(
        string='Claims Count',
        compute='_compute_counts'
    )
    warranty_record_ids = fields.Many2many(
        'solar.warranty.record',
        string='Active Warranty Certificates',
        compute='_compute_warranties'
    )
    active_warranty_count = fields.Integer(
        string='Active Warranties',
        compute='_compute_counts'
    )
    subsidy_case_ids = fields.One2many(
        'solar.subsidy.case',
        related='installation_id.subsidy_case_ids',
        string='Government Subsidy Cases'
    )

    # Digital Verification & QR Security
    verification_token = fields.Char(
        string='Digital Verification Token',
        copy=False,
        readonly=True,
        default=lambda self: uuid.uuid4().hex
    )
    verification_url = fields.Char(
        string='Public Passport Verification URL',
        compute='_compute_verification_url'
    )

    state = fields.Selection([
        ('draft', 'Draft Registration'),
        ('active', 'Active & Operational'),
        ('decommissioned', 'Decommissioned / Retired'),
    ], string='Status', default='active', required=True, tracking=True)

    notes = fields.Text(string='Lifecycle Remarks & Maintenance Notes')
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.passport') or _('New')
            if not vals.get('verification_token'):
                vals['verification_token'] = uuid.uuid4().hex
        return super().create(vals_list)

    @api.depends('component_ids', 'service_ticket_ids', 'warranty_record_ids')
    def _compute_counts(self):
        for rec in self:
            rec.component_count = len(rec.component_ids)
            rec.service_ticket_count = len(rec.service_ticket_ids)
            rec.active_warranty_count = len(rec.warranty_record_ids.filtered(lambda w: w.state == 'active'))

    @api.depends('component_ids.lot_id')
    def _compute_service_history(self):
        for rec in self:
            lots = rec.component_ids.mapped('lot_id')
            if lots:
                tickets = self.env['solar.service.ticket'].search([
                    '|',
                    ('lot_id', 'in', lots.ids),
                    ('partner_id', '=', rec.partner_id.id),
                ])
                rec.service_ticket_ids = tickets
            else:
                rec.service_ticket_ids = self.env['solar.service.ticket']

    @api.depends('component_ids.warranty_id')
    def _compute_warranties(self):
        for rec in self:
            warranties = rec.component_ids.mapped('warranty_id')
            rec.warranty_record_ids = warranties

    @api.depends('name', 'verification_token')
    def _compute_verification_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
        for rec in self:
            rec.verification_url = f"{base_url}/passport/verify/{rec.verification_token}"

    def action_decommission(self):
        """Mark solar installation passport as decommissioned or retired."""
        self.ensure_one()
        self.write({'state': 'decommissioned'})
        self.message_post(body=_("Digital Solar Passport marked as Decommissioned by %s.") % self.env.user.name)

    def action_reactivate(self):
        """Reactivate decommissioned solar passport."""
        self.ensure_one()
        self.write({'state': 'active'})
        self.message_post(body=_("Digital Solar Passport reactivated to Active status by %s.") % self.env.user.name)


class SolarPassportComponent(models.Model):
    """
    Component registry inside the Digital Solar Passport.
    Directly maps physical serialized hardware (inverters, batteries, charge controllers, panels)
    to its serial lot, warranty policy, and real-time validity status.
    """
    _name = 'solar.passport.component'
    _description = 'Digital Solar Passport Installed Component'
    _order = 'component_type, id'

    passport_id = fields.Many2one(
        'solar.passport',
        string='Digital Solar Passport',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Component Hardware',
        required=True
    )
    component_type = fields.Selection([
        ('inverter', 'Solar Inverter'),
        ('battery', 'Energy Storage Battery'),
        ('charge_controller', 'Charge Controller'),
        ('panel', 'Solar PV Panel'),
        ('bos', 'Balance of System & Wiring'),
        ('other', 'Other Component'),
    ], string='Component Category', default='inverter', required=True)

    lot_id = fields.Many2one(
        'stock.lot',
        string='Serial / Lot Number',
        required=True
    )
    serial_number = fields.Char(
        string='Serial Barcode',
        related='lot_id.name',
        store=True,
        readonly=True
    )
    warranty_id = fields.Many2one(
        'solar.warranty.record',
        string='Warranty Certificate'
    )
    warranty_status = fields.Selection([
        ('active', 'Under Active Warranty'),
        ('expired', 'Warranty Expired'),
        ('void', 'Warranty Voided'),
        ('no_warranty', 'No Warranty Policy'),
    ], string='Warranty Status', compute='_compute_warranty_status', store=True)

    warranty_end = fields.Date(
        string='Warranty Expiry Date',
        related='warranty_id.warranty_end',
        store=True,
        readonly=True
    )
    days_remaining = fields.Integer(
        string='Days Remaining',
        related='warranty_id.days_remaining',
        readonly=True
    )
    is_under_warranty = fields.Boolean(
        string='Is Currently Under Warranty',
        related='warranty_id.is_valid',
        readonly=True
    )
    installation_date = fields.Date(
        string='Installation Date',
        default=fields.Date.context_today
    )

    @api.depends('warranty_id', 'warranty_id.state', 'warranty_id.is_valid')
    def _compute_warranty_status(self):
        for comp in self:
            if comp.warranty_id:
                comp.warranty_status = comp.warranty_id.state
            else:
                comp.warranty_status = 'no_warranty'

