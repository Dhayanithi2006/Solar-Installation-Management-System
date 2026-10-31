# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SolarSiteSurvey(models.Model):
    _name = 'solar.site.survey'
    _description = 'Solar Rooftop Site Survey'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Survey Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string='Originating Opportunity / Lead',
        tracking=True
    )
    technician_id = fields.Many2one(
        'res.users',
        string='Assigned Survey Technician',
        tracking=True
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        tracking=True
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True
    )
    survey_date = fields.Date(
        string='Survey Scheduled Date',
        default=fields.Date.context_today,
        tracking=True
    )
    execution_date = fields.Datetime(
        string='Survey Conducted On',
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Solar Technical Assessment & Site Measurements
    requested_capacity_kw = fields.Float(
        string='System Capacity (kW)',
        default=3.0,
        tracking=True,
        help='Planned or requested solar capacity in kilowatts (1 kW to 5 kW).'
    )
    system_type = fields.Selection([
        ('on_grid', 'On-Grid'),
        ('off_grid', 'Off-Grid'),
    ], string='System Type', default='on_grid', tracking=True)

    monthly_bill_amount = fields.Monetary(
        string='Monthly Electricity Bill',
        currency_field='currency_id',
        tracking=True
    )
    shadow_free_roof_area = fields.Float(
        string='Shadow-Free Roof Area (Sq. Ft.)',
        tracking=True,
        help='Usable unshaded rooftop space measured by technician.'
    )
    grid_suitability = fields.Selection([
        ('suitable', 'Suitable (Standard Discom Grid)'),
        ('inspection_required', 'Inspection Required (Voltage/Transformer Check)'),
        ('unsuitable', 'Unsuitable for Net-Metering'),
    ], string='Grid Suitability', default='suitable', tracking=True)

    # Technician On-Site Measurements (Scenario 1)
    roof_direction = fields.Selection([
        ('south', 'South Facing (Optimal)'),
        ('south_east', 'South-East'),
        ('south_west', 'South-West'),
        ('east', 'East'),
        ('west', 'West'),
        ('flat', 'Flat Roof'),
        ('north', 'North (Sub-Optimal)'),
    ], string='Roof Direction / Orientation', tracking=True)

    roof_tilt = fields.Float(
        string='Roof Tilt Angle (Degrees)',
        default=15.0,
        tracking=True,
        help='Tilt angle in degrees from horizontal plane.'
    )
    cable_distance = fields.Float(
        string='Cable Distance to Inverter/Grid (Meters)',
        default=20.0,
        tracking=True,
        help='Estimated wiring run from rooftop array to inverter distribution point.'
    )
    roof_structure = fields.Selection([
        ('rcc', 'RCC Concrete Slab'),
        ('tin_shed', 'Industrial Tin / Metal Sheet'),
        ('tile', 'Sloped Clay Tile'),
        ('asbestos', 'Asbestos Sheet'),
        ('ground', 'Ground Mount Structure'),
    ], string='Roof Structure', default='rcc', tracking=True)

    shading_analysis = fields.Selection([
        ('no_shade', '100% Shadow-Free (9 AM - 4 PM)'),
        ('minor_shade', 'Minor Morning/Evening Shading (< 10%)'),
        ('significant_shade', 'Significant Obstruction (Shadow > 20%)'),
    ], string='Shading Analysis', default='no_shade', tracking=True)

    # Photo Evidence (Scenario 1)
    roof_photo = fields.Binary(
        string='Rooftop Photo Evidence',
        attachment=True,
        help='Visual proof of roof orientation, condition, and obstacles.'
    )
    meter_board_photo = fields.Binary(
        string='Discom Meter Board Photo',
        attachment=True,
        help='Visual proof of existing utility net meter board / connection.'
    )
    distribution_panel_photo = fields.Binary(
        string='Distribution Panel Photo',
        attachment=True,
        help='Visual proof of main AC distribution board and breaker rating.'
    )

    observations = fields.Text(
        string='Technician Observations & Notes',
        tracking=True
    )

    # Quotations Linkage & Gating
    sale_order_ids = fields.One2many(
        'sale.order',
        'survey_id',
        string='Generated Quotations'
    )
    quotation_count = fields.Integer(
        string='Quotations Count',
        compute='_compute_quotation_count'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.depends('sale_order_ids')
    def _compute_quotation_count(self):
        for record in self:
            record.quotation_count = len(record.sale_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.site.survey') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        """Technician submits survey for manager approval after validating measurements."""
        self.ensure_one()
        errors = []
        if not self.roof_direction:
            errors.append(_("Roof Direction / Orientation must be specified."))
        if self.shadow_free_roof_area <= 0:
            errors.append(_("Shadow-Free Roof Area must be greater than zero."))
        if self.cable_distance <= 0:
            errors.append(_("Cable Distance must be greater than zero."))
        if not (1.0 <= self.requested_capacity_kw <= 5.0):
            errors.append(_("System Capacity must be between 1.0 kW and 5.0 kW."))

        if errors:
            raise ValidationError("\n".join(errors))

        vals = {'state': 'submitted'}
        if not self.execution_date:
            vals['execution_date'] = fields.Datetime.now()
        self.write(vals)
        self.message_post(body=_("Survey submitted for managerial approval by %s.") % self.env.user.name)

    def action_approve(self):
        """Manager approves survey, unlocking quotation generation."""
        self.ensure_one()
        # Verify approver authority
        if not (self.env.user.has_group('solar_management.group_solar_survey_manager') or
                self.env.user.has_group('solar_management.group_solar_manager')):
            raise UserError(_("Access Denied: Only a Survey Approver or Manager can approve site surveys."))

        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'rejection_reason': False,
        })
        self.message_post(body=_(
            "Survey approved by %s on %s. Quotation generation unlocked."
        ) % (self.env.user.name, fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    def action_reject(self):
        """Manager rejects survey with feedback."""
        self.ensure_one()
        if not (self.env.user.has_group('solar_management.group_solar_survey_manager') or
                self.env.user.has_group('solar_management.group_solar_manager')):
            raise UserError(_("Access Denied: Only a Survey Approver or Manager can reject site surveys."))

        if not self.rejection_reason:
            raise UserError(_("Please provide a Rejection Reason explaining what corrections are required."))

        self.write({
            'state': 'rejected',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.message_post(body=_(
            "Survey rejected by %s. Reason: %s"
        ) % (self.env.user.name, self.rejection_reason))

    def action_reset_to_draft(self):
        """Technician resets survey to draft for revisions."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Survey reset to Draft for revision by %s.") % self.env.user.name)

    def action_create_quotation(self):
        """Generate a sales quotation from an approved site survey."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Cannot generate quotation: Site Survey '%s' is in state '%s'. "
                              "Quotations can only be generated after site survey approval.") % (self.name, self.state))

        order_vals = {
            'partner_id': self.partner_id.id,
            'opportunity_id': self.lead_id.id if self.lead_id else False,
            'survey_id': self.id,
            'company_id': self.company_id.id,
        }
        order = self.env['sale.order'].create(order_vals)
        self.message_post(body=_("Quotation %s generated from approved survey.") % order.name)

        return {
            'name': _('Solar Installation Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_quotations(self):
        """Smart button action to view linked quotations."""
        self.ensure_one()
        return {
            'name': _('Quotations for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('survey_id', '=', self.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_survey_id': self.id,
                'default_opportunity_id': self.lead_id.id if self.lead_id else False,
            },
        }
