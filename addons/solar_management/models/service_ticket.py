# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SolarServiceTicket(models.Model):
    _name = 'solar.service.ticket'
    _description = 'Solar Customer Service & Repair Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Ticket Reference',
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
    lot_id = fields.Many2one(
        'stock.lot',
        string='Reported Equipment Serial Number',
        tracking=True,
        help='Unique serial number of faulty inverter, battery, or charge controller.'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Equipment Product',
        tracking=True
    )
    component_type = fields.Selection(
        related='product_id.solar_component_type',
        string='Component Category',
        store=True,
        readonly=True
    )

    # Breakdown & Symptom Intake (Scenario 5: Rainy Season Breakdown)
    fault_category = fields.Selection([
        ('inverter_fault', 'Inverter Error / Red Light / No Generation'),
        ('battery_drain', 'Battery Fast Discharge / Not Holding Charge'),
        ('tripping', 'AC/DC MCB Breaker Tripping during Rain'),
        ('panel_damage', 'Physical Panel / Glass / Hotspot Damage'),
        ('controller_fault', 'Charge Controller Overvoltage / Flashing'),
        ('cable_fault', 'Wiring / Earthing / Connector Corrosion'),
        ('other', 'Other System Breakdown'),
    ], string='Fault Category', default='inverter_fault', required=True, tracking=True)

    reported_error_code = fields.Char(
        string='Fault Error Code (on LCD)',
        tracking=True,
        help='e.g. ERR-F04 (Grid Out of Range) or E02 (Battery Undervoltage).'
    )
    issue_description = fields.Text(
        string='Customer Breakdown Description',
        tracking=True
    )

    # Real-Time Warranty Verification (Scenario 5)
    warranty_id = fields.Many2one(
        'solar.warranty.record',
        string='Linked Warranty Certificate',
        compute='_compute_warranty_coverage',
        store=True,
        readonly=False,
        tracking=True
    )
    warranty_covered = fields.Boolean(
        string='Covered Under Warranty',
        compute='_compute_warranty_coverage',
        store=True,
        tracking=True
    )
    warranty_coverage_status = fields.Selection([
        ('covered', 'Under Active Warranty (₹0 Covered Repair)'),
        ('out_of_warranty', 'Out of Warranty (Chargeable Customer Billing)'),
        ('void', 'Warranty Voided (Chargeable Customer Billing)'),
    ], string='Warranty Decision', compute='_compute_warranty_coverage', store=True, tracking=True)

    # Operations & Assignment
    technician_id = fields.Many2one(
        'res.users',
        string='Assigned Service Technician',
        tracking=True
    )
    repair_id = fields.Many2one(
        'repair.order',
        string='Linked Repair Order',
        tracking=True
    )
    repair_ids = fields.One2many(
        'repair.order',
        'ticket_id',
        string='Repair Orders'
    )
    repair_count = fields.Integer(
        string='Repair Orders Count',
        compute='_compute_repair_count'
    )

    # Customer Resolution & Confirmation (Scenario 5 mandatory gate)
    customer_confirmed_resolution = fields.Boolean(
        string='Customer Confirmed Resolution',
        default=False,
        tracking=True,
        help='Customer confirms that the rooftop solar system has been restored to normal generation.'
    )
    customer_feedback = fields.Selection([
        ('excellent', 'Excellent — Fully Restored & Generating'),
        ('satisfactory', 'Satisfactory — Operational'),
        ('unsatisfactory', 'Unsatisfactory — Issue Persists'),
    ], string='Customer Feedback', tracking=True)

    customer_confirmation_notes = fields.Text(
        string='Confirmation Notes & Customer Remarks',
        tracking=True
    )
    resolution_date = fields.Datetime(
        string='Customer Confirmation Timestamp',
        readonly=True,
        tracking=True
    )

    state = fields.Selection([
        ('new', 'New Claim (Intake)'),
        ('assigned', 'Technician Assigned'),
        ('in_progress', 'Repair in Progress'),
        ('waiting_parts', 'Waiting for Replacement Hardware'),
        ('resolved', 'Resolved (Pending Customer Confirmation)'),
        ('closed', 'Closed & Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='new', required=True, tracking=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.depends('lot_id', 'lot_id.warranty_record_ids', 'partner_id')
    def _compute_warranty_coverage(self):
        """Instant warranty lookup by serial number and customer."""
        for ticket in self:
            if ticket.lot_id:
                # Find active warranty certificate for this serial
                warranty = self.env['solar.warranty.record'].search([
                    ('lot_id', '=', ticket.lot_id.id),
                    ('state', '=', 'active'),
                ], limit=1)

                if warranty:
                    ticket.warranty_id = warranty.id
                    ticket.warranty_covered = True
                    ticket.warranty_coverage_status = 'covered'
                else:
                    # Check if there is an expired or void warranty
                    any_warranty = ticket.lot_id.warranty_record_ids
                    if any_warranty and any_warranty[0].state == 'void':
                        ticket.warranty_id = any_warranty[0].id
                        ticket.warranty_covered = False
                        ticket.warranty_coverage_status = 'void'
                    else:
                        ticket.warranty_id = any_warranty[0].id if any_warranty else False
                        ticket.warranty_covered = False
                        ticket.warranty_coverage_status = 'out_of_warranty'
            else:
                ticket.warranty_id = False
                ticket.warranty_covered = False
                ticket.warranty_coverage_status = 'out_of_warranty'

    @api.constrains('partner_id', 'lot_id', 'product_id')
    def _check_service_ticket_relationships(self):
        """Enforce strict Scenario 5 consistency between customer, serial number, and product."""
        for ticket in self:
            if ticket.lot_id:
                # 1. Customer Serial Ownership Check
                if ticket.lot_id.customer_id and ticket.partner_id and ticket.lot_id.customer_id.id != ticket.partner_id.id:
                    raise ValidationError(_(
                        "Serial Number Conflict (Scenario 5):\n"
                        "Equipment serial '%s' is registered to customer '%s', not '%s'. "
                        "Service tickets cannot be raised against equipment owned by a different customer."
                    ) % (ticket.lot_id.name, ticket.lot_id.customer_id.name, ticket.partner_id.name))

                # 2. Product Serial Model Check
                if ticket.product_id and ticket.lot_id.product_id.id != ticket.product_id.id:
                    raise ValidationError(_(
                        "Product Conflict (Scenario 5):\n"
                        "Equipment serial '%s' belongs to product model '%s', but ticket product is set to '%s'."
                    ) % (ticket.lot_id.name, ticket.lot_id.product_id.name, ticket.product_id.name))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Filter serial numbers by customer when customer is selected."""
        if self.partner_id:
            # If current lot does not belong to partner, clear it
            if self.lot_id and self.lot_id.customer_id.id != self.partner_id.id:
                self.lot_id = False
            return {'domain': {'lot_id': [('customer_id', '=', self.partner_id.id)]}}
        return {'domain': {'lot_id': []}}

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """Auto-populate product and customer when serial number is scanned or selected."""
        if self.lot_id:
            self.product_id = self.lot_id.product_id.id
            if self.lot_id.customer_id and not self.partner_id:
                self.partner_id = self.lot_id.customer_id.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.service.ticket') or _('New')
        return super().create(vals_list)

    def action_assign(self):
        """Assign service technician to investigate breakdown."""
        self.ensure_one()
        self.state = 'assigned'
        self.message_post(body=_("Ticket assigned to service technician %s.") % (self.technician_id.name or "Unassigned"))

    def action_start_repair(self):
        """Technician begins diagnostic or repair work."""
        self.ensure_one()
        self.state = 'in_progress'

    def action_mark_resolved(self):
        """Technician marks repair as completed, moving to Resolved pending customer confirmation."""
        self.ensure_one()
        self.state = 'resolved'
        self.message_post(body=_(
            "Repair work finished by technician %s. Ticket is Resolved, awaiting customer generation confirmation."
        ) % self.env.user.name)

    def action_customer_confirm(self):
        """Record customer confirmation that system is generating power again."""
        self.ensure_one()
        self.write({
            'customer_confirmed_resolution': True,
            'resolution_date': fields.Datetime.now(),
            'customer_feedback': self.customer_feedback or 'excellent',
        })
        self.message_post(body=_(
            "Customer %s confirmed rooftop generation has been restored. Feedback: %s"
        ) % (self.partner_id.name, dict(self._fields['customer_feedback'].selection).get(self.customer_feedback, 'Confirmed')))

    def action_close(self):
        """Strict Scenario 5 Closure Gate: Ticket cannot close until customer confirmation is captured."""
        self.ensure_one()
        if not self.customer_confirmed_resolution:
            raise ValidationError(_(
                "Ticket Closure Blocked (Scenario 5):\n"
                "Customer confirmation is required before closing this service ticket. "
                "Please verify rooftop power generation with the customer and record customer confirmation."
            ))
        self.write({'state': 'closed'})
        self.message_post(body=_("Service ticket successfully closed following verified customer confirmation."))

    @api.depends('repair_ids')
    def _compute_repair_count(self):
        for ticket in self:
            ticket.repair_count = len(ticket.repair_ids)

    def action_create_repair_order(self):
        """Scenario 5: Generate Repair Order with real-time warranty verification and duplicate prevention."""
        self.ensure_one()
        if not self.product_id:
            raise UserError(_("Please specify the Equipment Product before creating a Repair Order."))

        # 1. Prevent duplicate repair order creation
        if self.repair_id and self.repair_id.exists() and self.repair_id.state not in ('cancel',):
            raise UserError(_(
                "A Repair Order (%s) is already actively linked to this service ticket. "
                "Duplicate repair orders cannot be created."
            ) % self.repair_id.name)

        # 2. Dynamic Real-Time Warranty Eligibility Re-verification
        today = fields.Date.today()
        active_warranty = False
        if self.lot_id:
            active_warranty = self.env['solar.warranty.record'].search([
                ('lot_id', '=', self.lot_id.id),
                ('state', '=', 'active'),
                ('warranty_start', '<=', today),
                ('warranty_end', '>=', today),
            ], limit=1)

        is_covered = bool(active_warranty)
        coverage_status = 'covered' if is_covered else (self.warranty_coverage_status or 'out_of_warranty')
        if not is_covered and coverage_status == 'covered':
            coverage_status = 'out_of_warranty'

        # 3. Determine warranty notes and billing classification
        if is_covered:
            notes = _(
                "₹0 WARRANTY COVERED REPAIR (Scenario 5):\n"
                "Equipment is operating under active warranty certificate '%s'.\n"
                "All replacement parts, diagnostic labor, and transit are covered at ₹0 cost to the customer."
            ) % active_warranty.name
        else:
            status_label = dict(self._fields['warranty_coverage_status'].selection).get(coverage_status, 'Out of Warranty')
            notes = _(
                "CHARGEABLE CUSTOMER REPAIR (Scenario 5):\n"
                "Equipment warranty status is '%s'.\n"
                "Replacement parts and technician service labor must be invoiced to the customer."
            ) % status_label

        repair_vals = {
            'ticket_id': self.id,
            'partner_id': self.partner_id.id,
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id if self.lot_id else False,
            'warranty_id': active_warranty.id if active_warranty else (self.warranty_id.id if self.warranty_id else False),
            'warranty_coverage_status': coverage_status,
            'warranty_notes': notes,
            'company_id': self.company_id.id,
        }
        repair = self.env['repair.order'].create(repair_vals)
        self.write({
            'repair_id': repair.id,
            'state': 'in_progress',
            'warranty_covered': is_covered,
            'warranty_coverage_status': coverage_status,
        })
        self.message_post(body=_(
            "Repair Order %s created. Billing Decision: %s."
        ) % (repair.name, dict(self._fields['warranty_coverage_status'].selection).get(coverage_status, '')))

        return {
            'name': _('Solar Equipment Repair'),
            'type': 'ir.actions.act_window',
            'res_model': 'repair.order',
            'res_id': repair.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_repair_orders(self):
        """Smart button action to view linked repair orders."""
        self.ensure_one()
        return {
            'name': _('Repair Orders for Ticket %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'repair.order',
            'view_mode': 'list,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {
                'default_ticket_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_product_id': self.product_id.id if self.product_id else False,
                'default_lot_id': self.lot_id.id if self.lot_id else False,
            },
        }

    def action_cancel(self):
        """Cancel service ticket."""
        self.ensure_one()
        self.write({'state': 'cancelled'})
