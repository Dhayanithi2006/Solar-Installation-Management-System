# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    requested_capacity_kw = fields.Float(
        string='Requested Capacity (kW)',
        default=3.0,
        tracking=True,
        help='System capacity requested by customer (1 kW to 5 kW).'
    )
    requested_system_type = fields.Selection([
        ('on_grid', 'On-Grid (Connected to Grid)'),
        ('off_grid', 'Off-Grid (Battery Storage)'),
    ], string='Requested System Type', default='on_grid', tracking=True)

    monthly_electricity_bill = fields.Monetary(
        string='Monthly Electricity Bill',
        currency_field='company_currency',
        tracking=True,
        help='Customer-reported average monthly electricity expenditure.'
    )
    shadow_free_roof_area = fields.Float(
        string='Shadow-Free Roof Space (Sq. Ft.)',
        tracking=True,
        help='Available unshaded roof area in square feet.'
    )
    grid_suitability = fields.Selection([
        ('suitable', 'Suitable (Standard Discom Grid)'),
        ('inspection_required', 'Inspection Required (Voltage/Transformer Check)'),
        ('unsuitable', 'Unsuitable for Net-Metering'),
    ], string='Grid Suitability Assessment', default='suitable', tracking=True)

    subsidy_interest = fields.Boolean(
        string='Interested in Government Subsidy',
        default=True,
        tracking=True,
        help='Customer wishes to apply for the Central/State Rooftop Solar Subsidy scheme.'
    )
    roof_space_notes = fields.Text(
        string='Roof Observations & Notes',
        help='Details on roof structure (RCC, tin shed, tiled), shading trees, or nearby obstacles.'
    )
    survey_ids = fields.One2many(
        'solar.site.survey',
        'lead_id',
        string='Rooftop Site Surveys'
    )
    survey_count = fields.Integer(
        string='Survey Count',
        compute='_compute_survey_count'
    )
    survey_status = fields.Selection([
        ('no_survey', 'No Survey Requested'),
        ('draft', 'Survey in Draft'),
        ('submitted', 'Survey Submitted (Pending Approval)'),
        ('approved', 'Survey Approved (Ready for Quote)'),
        ('rejected', 'Survey Rejected (Correction Required)'),
    ], string='Survey Status', compute='_compute_survey_status', store=True, tracking=True)

    @api.depends('survey_ids')
    def _compute_survey_count(self):
        for lead in self:
            lead.survey_count = len(lead.survey_ids)

    @api.depends('survey_ids.state')
    def _compute_survey_status(self):
        for lead in self:
            if not lead.survey_ids:
                lead.survey_status = 'no_survey'
            else:
                latest_survey = lead.survey_ids.sorted('id', reverse=True)[0]
                lead.survey_status = latest_survey.state

    def action_create_site_survey(self):
        """Action button to create a site survey pre-populated with customer and solar requirements."""
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            # Auto-create or link customer from lead contact details
            partner = self._create_customer_from_lead()

        survey_vals = {
            'lead_id': self.id,
            'partner_id': partner.id,
            'requested_capacity_kw': self.requested_capacity_kw,
            'system_type': self.requested_system_type,
            'monthly_bill_amount': self.monthly_electricity_bill,
            'shadow_free_roof_area': self.shadow_free_roof_area,
            'grid_suitability': self.grid_suitability,
            'company_id': self.company_id.id or self.env.company.id,
        }
        survey = self.env['solar.site.survey'].create(survey_vals)
        return {
            'name': _('Rooftop Site Survey'),
            'view_mode': 'form',
            'res_model': 'solar.site.survey',
            'res_id': survey.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def _create_customer_from_lead(self):
        """Ensure a res.partner exists for the lead."""
        self.ensure_one()
        partner_vals = {
            'name': self.contact_name or self.partner_name or self.name,
            'phone': self.phone or self.mobile,
            'email': self.email_from,
            'street': self.street,
            'city': self.city,
            'customer_rank': 1,
        }
        partner = self.env['res.partner'].create(partner_vals)
        self.partner_id = partner.id
        return partner

    def action_view_surveys(self):
        """Smart button action to view linked surveys."""
        self.ensure_one()
        return {
            'name': _('Site Surveys for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.site.survey',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id, 'default_partner_id': self.partner_id.id},
        }

