# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SolarSubsidyDocumentType(models.Model):
    _name = 'solar.subsidy.document.type'
    _description = 'Solar Subsidy Required Document Type'
    _order = 'sequence, name'

    name = fields.Char(string='Document Name', required=True)
    code = fields.Char(string='Document Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    is_mandatory = fields.Boolean(string='Mandatory for Approval', default=True)
    description = fields.Text(string='Guidelines')
    active = fields.Boolean(default=True)


class SolarSubsidyDocument(models.Model):
    _name = 'solar.subsidy.document'
    _description = 'Solar Subsidy Applicant Document Checklist'
    _order = 'case_id, sequence, id'

    case_id = fields.Many2one(
        'solar.subsidy.case',
        string='Subsidy Case',
        required=True,
        ondelete='cascade'
    )
    document_type_id = fields.Many2one(
        'solar.subsidy.document.type',
        string='Document Type',
        required=True
    )
    sequence = fields.Integer(
        related='document_type_id.sequence',
        store=True,
        readonly=True
    )
    is_mandatory = fields.Boolean(
        related='document_type_id.is_mandatory',
        store=True,
        readonly=True
    )
    attachment = fields.Binary(
        string='Document File',
        attachment=True
    )
    filename = fields.Char(string='File Name')
    state = fields.Selection([
        ('pending', 'Pending Upload'),
        ('uploaded', 'Uploaded (Pending Review)'),
        ('verified', 'Verified & Valid'),
        ('rejected', 'Rejected / Incomplete'),
    ], string='Status', default='pending', required=True, tracking=True)

    verified_by = fields.Many2one('res.users', string='Verified By', readonly=True)
    verified_date = fields.Datetime(string='Verification Date', readonly=True)
    notes = fields.Char(string='Reviewer Remarks')

    @api.onchange('attachment')
    def _onchange_attachment(self):
        if self.attachment and self.state == 'pending':
            self.state = 'uploaded'

    def action_verify(self):
        """Reviewer confirms document satisfies statutory DISCOM requirement."""
        self.ensure_one()
        self.write({
            'state': 'verified',
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now(),
        })

    def action_reject(self):
        """Reviewer rejects document due to blurriness, mismatch, or expiry."""
        self.ensure_one()
        self.write({
            'state': 'rejected',
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now(),
        })


class SolarSubsidyCase(models.Model):
    _name = 'solar.subsidy.case'
    _description = 'Solar Government Subsidy Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Subsidy Case Ref',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer Applicant',
        required=True,
        tracking=True
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Source Sales Order',
        tracking=True
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Linked Installation Job',
        compute='_compute_installation_id',
        store=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )

    # Discom & National Scheme Details
    application_number = fields.Char(
        string='National Portal Ref # (PM Surya Ghar)',
        tracking=True,
        help='Reference number generated upon filing on the PM Surya Ghar / National Rooftop Solar Portal.'
    )
    scheme_name = fields.Char(
        string='Subsidy Scheme',
        default='PM Surya Ghar: Muft Bijli Yojana',
        tracking=True
    )
    discom_name = fields.Selection([
        ('tsspdcl', 'TSSPDCL (Telangana Southern Power)'),
        ('tsnpdcl', 'TSNPDCL (Telangana Northern Power)'),
        ('bescom', 'BESCOM (Bangalore Electricity Supply)'),
        ('tangedco', 'TANGEDCO (Tamil Nadu Electricity Board)'),
        ('msedcl', 'MSEDCL / Mahavitaran (Maharashtra)'),
        ('tatapower', 'Tata Power / Adani Electricity'),
        ('other', 'Other State DISCOM'),
    ], string='Electricity DISCOM', default='tsspdcl', tracking=True)

    consumer_number = fields.Char(
        string='Electricity Service Connection No (SC No)',
        tracking=True,
        help='Unique consumer service connection number on the customer electricity bill.'
    )

    # Capacity & Direct Benefit Sizing
    solar_capacity_kw = fields.Float(
        string='Rooftop Solar Capacity (kW)',
        compute='_compute_capacity',
        store=True,
        tracking=True,
        help='Installed or ordered solar capacity in kW.'
    )
    eligible_subsidy_amount = fields.Monetary(
        string='Eligible Central Subsidy (₹)',
        compute='_compute_eligible_subsidy',
        store=True,
        currency_field='currency_id',
        tracking=True,
        help='Central Financial Assistance (CFA) calculated per PM Surya Ghar guidelines:\n- 1 kW: ₹30,000\n- 2 kW: ₹60,000\n- 3 kW to 5 kW: ₹78,000 maximum standard direct benefit.'
    )
    sanctioned_amount = fields.Monetary(
        string='Sanctioned Subsidy (₹)',
        currency_field='currency_id',
        tracking=True,
        help='Subsidy amount officially sanctioned following DISCOM joint site inspection.'
    )
    disbursed_amount = fields.Monetary(
        string='Disbursed Subsidy (DBT ₹)',
        currency_field='currency_id',
        tracking=True,
        help='Amount directly credited to customer bank account via DBT.'
    )
    disbursement_date = fields.Date(
        string='DBT Credit Date',
        tracking=True
    )
    disbursement_reference = fields.Char(
        string='Bank UTR / Direct Credit Ref #',
        tracking=True
    )

    # Document Checklist & Verification Gate
    document_ids = fields.One2many(
        'solar.subsidy.document',
        'case_id',
        string='Applicant Documentation Checklist'
    )
    document_count = fields.Integer(
        string='Total Documents Count',
        compute='_compute_document_status'
    )
    mandatory_docs_verified = fields.Boolean(
        string='All Mandatory Documents Verified',
        compute='_compute_document_status',
        store=True,
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Document Gathering'),
        ('submitted', 'Submitted to DISCOM Portal'),
        ('under_review', 'Joint Site Inspection / Review'),
        ('approved', 'Subsidy Sanctioned'),
        ('disbursed', 'Direct Benefit Disbursed (DBT)'),
        ('rejected', 'Application Rejected'),
    ], string='Status', default='draft', required=True, tracking=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.depends('sale_order_id', 'sale_order_id.installation_ids')
    def _compute_installation_id(self):
        for case in self:
            if case.sale_order_id and case.sale_order_id.installation_ids:
                case.installation_id = case.sale_order_id.installation_ids[0].id
            else:
                case.installation_id = False

    @api.depends('installation_id.installed_capacity_kw', 'sale_order_id.package_id.capacity_kw', 'sale_order_id.survey_id.requested_capacity_kw')
    def _compute_capacity(self):
        for case in self:
            cap = 0.0
            if case.installation_id and case.installation_id.installed_capacity_kw:
                cap = case.installation_id.installed_capacity_kw
            elif case.sale_order_id and case.sale_order_id.package_id:
                cap = case.sale_order_id.package_id.capacity_kw
            elif case.sale_order_id and case.sale_order_id.survey_id:
                cap = case.sale_order_id.survey_id.requested_capacity_kw
            case.solar_capacity_kw = cap or 3.0

    @api.depends('solar_capacity_kw')
    def _compute_eligible_subsidy(self):
        """Calculate PM Surya Ghar DBT Central Subsidy based on capacity tiers."""
        for case in self:
            cap = case.solar_capacity_kw or 0.0
            if cap <= 0:
                sub = 0.0
            elif cap <= 1.0:
                sub = 30000.0
            elif cap <= 2.0:
                sub = 60000.0
            else:
                # 3 kW and above up to 5 kW gets maximum ₹78,000 standard DBT
                sub = 78000.0
            case.eligible_subsidy_amount = sub

    @api.depends('document_ids.state', 'document_ids.is_mandatory')
    def _compute_document_status(self):
        for case in self:
            case.document_count = len(case.document_ids)
            mand_docs = case.document_ids.filtered(lambda d: d.is_mandatory)
            if not mand_docs:
                case.mandatory_docs_verified = False
            else:
                case.mandatory_docs_verified = all(d.state == 'verified' for d in mand_docs)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.subsidy.case') or _('New')
        cases = super().create(vals_list)
        for case in cases:
            if not case.document_ids:
                case.action_generate_required_documents()
        return cases

    def action_generate_required_documents(self):
        """Pre-populate required document checklist lines from active document types."""
        self.ensure_one()
        doc_types = self.env['solar.subsidy.document.type'].search([('active', '=', True)])
        existing_types = self.document_ids.mapped('document_type_id.id')
        new_docs = []
        for dtype in doc_types:
            if dtype.id not in existing_types:
                new_docs.append((0, 0, {
                    'document_type_id': dtype.id,
                    'state': 'pending',
                }))
        if new_docs:
            self.write({'document_ids': new_docs})
            self.message_post(body=_("PM Surya Ghar document checklist generated (%d items).") % len(new_docs))

    def action_submit(self):
        """Submit to DISCOM portal; enforce strict mandatory document verification gate."""
        self.ensure_one()
        if not self.application_number:
            raise ValidationError(_("Please record the Government / DISCOM Application Reference Number before submitting."))
        if not self.consumer_number:
            raise ValidationError(_("Please record the customer's Electricity Service Connection Number (SC No)."))

        unverified = self.document_ids.filtered(lambda d: d.is_mandatory and d.state != 'verified')
        if unverified:
            names = ", ".join(unverified.mapped('document_type_id.name'))
            raise ValidationError(_(
                "Submission Blocked:\n"
                "The following mandatory documents must be uploaded and verified before submission to DISCOM:\n- %s"
            ) % names)

        self.write({
            'state': 'submitted',
        })
        self.message_post(body=_(
            "Subsidy Application submitted to %s portal under Ref: %s. All %d mandatory documents verified."
        ) % (
            dict(self._fields['discom_name'].selection).get(self.discom_name, self.discom_name),
            self.application_number,
            len(self.document_ids.filtered(lambda d: d.is_mandatory))
        ))

    def action_start_review(self):
        """Technician/Inspector initiates joint site inspection."""
        self.ensure_one()
        self.state = 'under_review'
        self.message_post(body=_("Application is under joint site inspection and review by DISCOM electrical inspectors."))

    def action_approve_sanction(self):
        """Record official subsidy sanction letter from DISCOM/MNRE."""
        self.ensure_one()
        vals = {'state': 'approved'}
        if not self.sanctioned_amount:
            vals['sanctioned_amount'] = self.eligible_subsidy_amount
        self.write(vals)
        self.message_post(body=_(
            "Subsidy sanctioned by DISCOM/MNRE for %s! Sanction letter received."
        ) % self.currency_id.format(self.sanctioned_amount))

    def action_record_disbursement(self):
        """Confirm Direct Benefit Transfer (DBT) payout into customer account."""
        self.ensure_one()
        vals = {'state': 'disbursed'}
        if not self.disbursed_amount:
            vals['disbursed_amount'] = self.sanctioned_amount or self.eligible_subsidy_amount
        if not self.disbursement_date:
            vals['disbursement_date'] = fields.Date.context_today(self)
        if not self.disbursement_reference:
            vals['disbursement_reference'] = _("DBT-DIRECT-CREDIT")
        self.write(vals)
        self.message_post(body=_(
            "Direct Benefit Transfer (DBT) confirmed! Customer received %s in bank account on %s (UTR Ref: %s)."
        ) % (
            self.currency_id.format(self.disbursed_amount),
            self.disbursement_date,
            self.disbursement_reference
        ))

    def action_reject(self):
        """Record application rejection."""
        self.ensure_one()
        self.state = 'rejected'
        self.message_post(body=_("Subsidy application rejected by DISCOM/Nodal Agency."))
