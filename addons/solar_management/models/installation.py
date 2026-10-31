# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SolarInstallation(models.Model):
    _name = 'solar.installation'
    _description = 'Solar Installation Job'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Installation Reference',
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
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Source Order',
        required=True,
        tracking=True
    )
    survey_id = fields.Many2one(
        'solar.site.survey',
        string='Approved Survey',
        tracking=True
    )

    # Crew & Scheduling (15-technician pool)
    lead_technician_id = fields.Many2one(
        'res.users',
        string='Lead Technician',
        tracking=True
    )
    technician_ids = fields.Many2many(
        'res.users',
        'solar_installation_technician_rel',
        'installation_id',
        'user_id',
        string='Assigned Crew Members',
        tracking=True
    )
    planned_start = fields.Datetime(
        string='Scheduled Start Time',
        tracking=True
    )
    planned_finish = fields.Datetime(
        string='Scheduled Finish Time',
        tracking=True
    )
    actual_start = fields.Datetime(
        string='Actual Work Start',
        tracking=True
    )
    actual_finish = fields.Datetime(
        string='Actual Work Finish',
        tracking=True
    )
    duration_hours = fields.Float(
        string='Actual Duration (Hours)',
        compute='_compute_duration_hours',
        store=True,
        tracking=True
    )

    # Logistics & Equipment Integration
    picking_ids = fields.One2many(
        'stock.picking',
        'installation_id',
        string='Delivery Pickings'
    )
    picking_count = fields.Integer(
        string='Pickings Count',
        compute='_compute_picking_count'
    )
    lot_ids = fields.Many2many(
        'stock.lot',
        string='Delivered & Installed Serial Numbers',
        compute='_compute_installed_lots',
        store=True,
        help='Serial numbers of inverters, batteries, and controllers delivered and mounted.'
    )
    subsidy_case_ids = fields.One2many(
        'solar.subsidy.case',
        'installation_id',
        string='Subsidy Cases'
    )
    subsidy_case_count = fields.Integer(
        string='Subsidy Cases Count',
        compute='_compute_subsidy_case_count'
    )
    passport_id = fields.Many2one(
        'solar.passport',
        string='Digital Solar Passport',
        copy=False,
        readonly=True
    )
    passport_count = fields.Integer(
        string='Passports Count',
        compute='_compute_passport_count'
    )
    hardware_delivered = fields.Boolean(
        string='Hardware Delivered on Site',
        compute='_compute_hardware_delivered',
        store=True,
        tracking=True
    )

    # Technical Specifications & Power Generation Test (Scenario 4)
    installed_capacity_kw = fields.Float(
        string='Installed Capacity (kW)',
        default=3.0,
        tracking=True
    )
    test_dc_voltage = fields.Float(
        string='Measured DC String Voltage (V)',
        tracking=True,
        help='Measured open-circuit / operational DC voltage from the solar PV array.'
    )
    test_ac_voltage = fields.Float(
        string='Measured AC Grid Voltage (V)',
        default=230.0,
        tracking=True,
        help='Measured AC grid line voltage at the inverter distribution box.'
    )
    test_generation_kw = fields.Float(
        string='Peak Test Generation (kW)',
        tracking=True,
        help='Active power generation recorded during the commissioning load test.'
    )
    generation_confirmed = fields.Boolean(
        string='Power Generation Test Confirmed',
        tracking=True,
        help='Technician certifies that system is generating active power and synchronized to grid/load.'
    )
    test_result = fields.Selection([
        ('passed', 'Passed (Nominal Output Achieved)'),
        ('passed_conditional', 'Passed with Shading Notice'),
        ('failed', 'Failed (Re-Inspection Required)'),
    ], string='Test Result', default='passed', tracking=True)

    technician_notes = fields.Text(
        string='Technician Observations & Notes',
        tracking=True
    )

    # Mobile Geo-Coordinates on Roof (Scenario 4)
    gps_latitude = fields.Float(
        string='Commissioning GPS Latitude',
        digits=(10, 6),
        tracking=True,
        help='Latitude recorded on-site during rooftop commissioning.'
    )
    gps_longitude = fields.Float(
        string='Commissioning GPS Longitude',
        digits=(10, 6),
        tracking=True,
        help='Longitude recorded on-site during rooftop commissioning.'
    )
    gps_required = fields.Boolean(
        string='GPS Coordinates Mandatory',
        default=True,
        help='Whether valid GPS coordinates must be recorded before commissioning.'
    )

    # Photographic Evidence Attachments (Scenario 4)
    installation_photo_array = fields.Binary(
        string='Mounted Solar Array Photo',
        attachment=True,
        help='Photographic proof of roof array mounting, tilt, and clamps.'
    )
    installation_photo_inverter = fields.Binary(
        string='Inverter & AC/DC Box Photo',
        attachment=True,
        help='Photographic proof of wall-mounted inverter and electrical safety wiring.'
    )
    installation_photo_generation = fields.Binary(
        string='Live Generation Display Photo',
        attachment=True,
        help='Photographic proof of live kW generation reading on inverter/meter LCD.'
    )

    # Customer On-Screen Acceptance Signature (DEC-009 & Scenario 4)
    customer_signature = fields.Binary(
        string='Customer Acceptance Signature',
        attachment=True,
        copy=False,
        help='Customer digital signature acknowledging successful rooftop commissioning.'
    )
    customer_signed_by = fields.Char(
        string='Signed By Customer Name',
        tracking=True
    )
    customer_signed_date = fields.Datetime(
        string='Signed On Date',
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Draft (Pending Dispatch)'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress (On Roof)'),
        ('submitted', 'Submitted for Review'),
        ('completed', 'Completed & Commissioned'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )
    active = fields.Boolean(default=True)

    # Invoices & Direct Project Expenses Linkages
    invoice_ids = fields.One2many(
        'account.move',
        'installation_id',
        string='Customer Invoices',
        domain=[('move_type', 'in', ('out_invoice', 'out_refund'))]
    )
    invoice_count = fields.Integer(
        string='Customer Invoices Count',
        compute='_compute_invoice_count'
    )
    expense_ids = fields.One2many(
        'account.move',
        'installation_id',
        string='Direct Project Expenses',
        domain=[('move_type', 'in', ('in_invoice', 'in_refund'))]
    )
    expense_count = fields.Integer(
        string='Direct Expenses Count',
        compute='_compute_expense_count'
    )

    # Labor Costing Inputs
    technician_hourly_rate = fields.Float(
        string='Technician Labor Rate (₹/hr)',
        default=500.0,
        tracking=True,
        help='Standard labor rate per technician hour for solar rooftop installation.'
    )
    num_technicians = fields.Integer(
        string='Assigned Crew Count',
        compute='_compute_technician_headcount',
        store=True,
        help='Headcount of lead technician plus crew members assigned to this installation.'
    )

    # Financial Costing Metrics (DEC-007 / Scenario 6)
    revenue_invoiced = fields.Monetary(
        string='Invoiced Revenue (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id',
        tracking=True,
        help='Total invoiced revenue from posted customer invoices.'
    )
    cost_materials = fields.Monetary(
        string='Material COGS (₹)',
        compute='_compute_project_financials',
        store=True,
        readonly=False,
        currency_field='currency_id',
        tracking=True,
        help='Hardware Cost of Goods Sold from delivered Bill of Materials / stock pickings.'
    )
    cost_technician_labor = fields.Monetary(
        string='Technician Labor Cost (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id',
        tracking=True,
        help='Calculated as: Actual Duration (Hours) x Hourly Rate x Crew Count.'
    )
    cost_freight = fields.Monetary(
        string='Freight & Logistics Cost (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id'
    )
    cost_permits = fields.Monetary(
        string='Permits & Net-Metering Cost (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id'
    )
    cost_inspection = fields.Monetary(
        string='Safety Inspection Cost (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id'
    )
    cost_other_expenses = fields.Monetary(
        string='Other Direct Expenses (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id'
    )
    cost_direct_expenses = fields.Monetary(
        string='Attributable Direct Expenses (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id',
        tracking=True,
        help='Sum of posted vendor bills for transport, permits, safety inspection, and consumables.'
    )
    cost_total_direct = fields.Monetary(
        string='Total Direct Cost (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id',
        tracking=True,
        help='Total Direct Project Cost = Material COGS + Technician Labor + Attributable Direct Expenses.'
    )
    gross_margin = fields.Monetary(
        string='Gross Margin (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id',
        tracking=True,
        help='Tier 1 Profitability: Invoiced Revenue - Material COGS.'
    )
    gross_margin_pct = fields.Float(
        string='Gross Margin (%)',
        compute='_compute_project_financials',
        store=True,
        digits=(5, 2),
        tracking=True
    )
    contribution_profit = fields.Monetary(
        string='Installation Contribution Profit (₹)',
        compute='_compute_project_financials',
        store=True,
        currency_field='currency_id',
        tracking=True,
        help='Tier 2 Profitability (DEC-007): Invoiced Revenue - Material COGS - Technician Labor - Attributable Direct Expenses.'
    )
    contribution_margin_pct = fields.Float(
        string='Contribution Margin (%)',
        compute='_compute_project_financials',
        store=True,
        digits=(5, 2),
        tracking=True
    )
    profitability_status = fields.Selection([
        ('healthy', 'Healthy (>20% Contribution)'),
        ('acceptable', 'Acceptable (10-20% Contribution)'),
        ('low', 'Low Margin (0-10% Contribution)'),
        ('negative', 'Deficit / Loss (<0%)'),
    ], string='Profitability Status', compute='_compute_project_financials', store=True, tracking=True)

    @api.depends('actual_start', 'actual_finish')
    def _compute_duration_hours(self):
        for inst in self:
            if inst.actual_start and inst.actual_finish:
                delta = inst.actual_finish - inst.actual_start
                inst.duration_hours = round(delta.total_seconds() / 3600.0, 2)
            else:
                inst.duration_hours = 0.0

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for inst in self:
            inst.invoice_count = len(inst.invoice_ids)

    @api.depends('expense_ids')
    def _compute_expense_count(self):
        for inst in self:
            inst.expense_count = len(inst.expense_ids)

    @api.depends('passport_id')
    def _compute_passport_count(self):
        for inst in self:
            inst.passport_count = 1 if inst.passport_id else 0

    @api.depends('subsidy_case_ids')
    def _compute_subsidy_case_count(self):
        for inst in self:
            inst.subsidy_case_count = len(inst.subsidy_case_ids)

    @api.depends('lead_technician_id', 'technician_ids')
    def _compute_technician_headcount(self):
        for inst in self:
            crew = set()
            if inst.lead_technician_id:
                crew.add(inst.lead_technician_id.id)
            if inst.technician_ids:
                crew.update(inst.technician_ids.ids)
            inst.num_technicians = len(crew) if crew else 1

    @api.depends(
        'invoice_ids.state', 'invoice_ids.amount_untaxed', 'invoice_ids.amount_total',
        'sale_order_id.invoice_ids.state', 'sale_order_id.invoice_ids.amount_untaxed',
        'expense_ids.state', 'expense_ids.amount_untaxed', 'expense_ids.amount_total',
        'duration_hours', 'technician_hourly_rate', 'num_technicians',
        'picking_ids.state', 'picking_ids.move_ids.quantity', 'picking_ids.move_ids.product_id.standard_price',
        'sale_order_id.package_id.standard_price'
    )
    def _compute_project_financials(self):
        for inst in self:
            # 1. Invoiced Customer Revenue (Tier 1 & 2 baseline)
            invoices = inst.invoice_ids | inst.sale_order_id.invoice_ids.filtered(lambda inv: inv.move_type in ('out_invoice', 'out_refund'))
            posted_invoices = invoices.filtered(lambda inv: inv.state == 'posted')
            if posted_invoices:
                rev = sum(inv.amount_untaxed for inv in posted_invoices)
            else:
                draft_invoices = invoices.filtered(lambda inv: inv.state != 'cancel')
                if draft_invoices:
                    rev = sum(inv.amount_untaxed for inv in draft_invoices)
                elif inst.sale_order_id:
                    rev = inst.sale_order_id.amount_untaxed or inst.sale_order_id.amount_total
                else:
                    rev = 0.0
            inst.revenue_invoiced = rev

            # 2. Material COGS (Hardware Delivery Cost)
            done_pickings = inst.picking_ids.filtered(lambda p: p.state == 'done')
            mat_cost = 0.0
            if done_pickings:
                for move in done_pickings.mapped('move_ids'):
                    mat_cost += (move.quantity or move.product_uom_qty) * (move.product_id.standard_price or 0.0)
            if not mat_cost and inst.sale_order_id and inst.sale_order_id.package_id:
                mat_cost = inst.sale_order_id.package_id.standard_price
            if not mat_cost and inst.cost_materials:
                mat_cost = inst.cost_materials
            inst.cost_materials = mat_cost

            # 3. Technician Labor Cost (Hours x Rate x Headcount)
            hours = inst.duration_hours or 0.0
            rate = inst.technician_hourly_rate or 500.0
            headcount = inst.num_technicians or 1
            inst.cost_technician_labor = round(hours * rate * headcount, 2)

            # 4. Attributable Direct Project Expenses (Vendor Bills)
            bills = inst.expense_ids.filtered(lambda b: b.state != 'cancel')
            freight = sum(abs(b.amount_untaxed or b.amount_total) for b in bills if b.solar_expense_type == 'freight')
            permits = sum(abs(b.amount_untaxed or b.amount_total) for b in bills if b.solar_expense_type in ('permit', 'liaison'))
            inspection = sum(abs(b.amount_untaxed or b.amount_total) for b in bills if b.solar_expense_type == 'inspection')
            others = sum(abs(b.amount_untaxed or b.amount_total) for b in bills if b.solar_expense_type in ('consumables', 'other', False))

            inst.cost_freight = freight
            inst.cost_permits = permits
            inst.cost_inspection = inspection
            inst.cost_other_expenses = others
            inst.cost_direct_expenses = freight + permits + inspection + others

            # 5. Total Direct Installation Cost
            inst.cost_total_direct = inst.cost_materials + inst.cost_technician_labor + inst.cost_direct_expenses

            # 6. Tier 1: Gross Margin
            inst.gross_margin = inst.revenue_invoiced - inst.cost_materials
            inst.gross_margin_pct = round((inst.gross_margin / inst.revenue_invoiced * 100.0), 2) if inst.revenue_invoiced else 0.0

            # 7. Tier 2 (DEC-007): Installation Contribution Profit
            inst.contribution_profit = inst.revenue_invoiced - inst.cost_total_direct
            inst.contribution_margin_pct = round((inst.contribution_profit / inst.revenue_invoiced * 100.0), 2) if inst.revenue_invoiced else 0.0

            # 8. Profitability Status Classification
            if inst.revenue_invoiced <= 0:
                inst.profitability_status = 'acceptable'
            elif inst.contribution_margin_pct >= 20.0:
                inst.profitability_status = 'healthy'
            elif inst.contribution_margin_pct >= 10.0:
                inst.profitability_status = 'acceptable'
            elif inst.contribution_margin_pct >= 0.0:
                inst.profitability_status = 'low'
            else:
                inst.profitability_status = 'negative'

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for inst in self:
            inst.picking_count = len(inst.picking_ids)

    @api.depends('picking_ids.move_line_ids.lot_id', 'picking_ids.state')
    def _compute_installed_lots(self):
        for inst in self:
            lots = inst.picking_ids.filtered(lambda p: p.state == 'done').mapped('move_line_ids.lot_id')
            inst.lot_ids = lots

    @api.depends('picking_ids.state')
    def _compute_hardware_delivered(self):
        for inst in self:
            inst.hardware_delivered = any(p.state == 'done' for p in inst.picking_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.installation') or _('New')
        return super().create(vals_list)

    def action_schedule(self):
        """Schedule installation job once hardware dispatch is underway."""
        self.ensure_one()
        self.state = 'scheduled'

    def action_start_work(self):
        """Technician commences physical installation on customer rooftop."""
        self.ensure_one()
        vals = {'state': 'in_progress'}
        if not self.actual_start:
            vals['actual_start'] = fields.Datetime.now()
        self.write(vals)
        tech_name = self.lead_technician_id.name or self.env.user.name
        self.message_post(body=_("Installation work started on roof by lead technician %s.") % tech_name)

    def action_submit_review(self):
        """Technician finishes rooftop work and submits for review."""
        self.ensure_one()
        vals = {'state': 'submitted'}
        if not self.actual_finish:
            vals['actual_finish'] = fields.Datetime.now()
        self.write(vals)
        self.message_post(body=_("Installation worksheet submitted for final review by %s.") % self.env.user.name)

    def action_complete(self):
        """Enforce Scenario 4 completion gate: crew assignment, hardware delivery, electrical measurements, GPS, photo evidence, and customer acceptance signature."""
        self.ensure_one()
        missing = []

        # 1. Assigned Crew
        if not self.lead_technician_id and not self.technician_ids:
            missing.append(_("Assigned Lead Technician or Crew members must be specified."))

        # 2. Hardware Delivery on Site
        if self.picking_ids and not self.hardware_delivered:
            missing.append(_("Hardware delivery on site must be confirmed (hardware transfers must be completed)."))

        # 3. Electrical Power Measurements
        if not self.generation_confirmed:
            missing.append(_("Power Generation Test must be confirmed."))
        if self.test_generation_kw <= 0:
            missing.append(_("Peak Test Generation (kW) must be greater than zero."))
        if self.test_dc_voltage <= 0:
            missing.append(_("Measured DC String Voltage (V) must be greater than zero."))
        if self.test_ac_voltage <= 0:
            missing.append(_("Measured AC Grid Voltage (V) must be greater than zero."))

        # 4. GPS Details
        if self.gps_required and (not self.gps_latitude or not self.gps_longitude):
            missing.append(_("On-roof GPS Latitude and Longitude coordinates must be captured."))

        # 5. Customer Digital Sign-Off
        if not self.customer_signature:
            missing.append(_("Customer Acceptance Signature must be captured."))

        # 6. Photographic Evidence
        if not (self.installation_photo_array or self.installation_photo_inverter):
            missing.append(_("At least one installation photograph (Array or Inverter) must be attached."))

        if missing:
            raise ValidationError(_(
                "Installation Completion Blocked (Scenario 4):\n"
                "The following evidence requirements must be satisfied before marking the installation as completed:\n- %s"
            ) % "\n- ".join(missing))

        vals = {'state': 'completed'}
        if not self.actual_finish:
            vals['actual_finish'] = fields.Datetime.now()
        if not self.customer_signed_date:
            vals['customer_signed_date'] = fields.Datetime.now()
        if not self.customer_signed_by:
            vals['customer_signed_by'] = self.partner_id.name

        self.write(vals)

        # Synchronize installation reference to delivered serial warranty records
        for picking in self.picking_ids:
            for line in picking.move_line_ids.filtered(lambda l: l.lot_id):
                warranties = self.env['solar.warranty.record'].search([('lot_id', '=', line.lot_id.id)])
                for w in warranties:
                    if not w.installation_id:
                        w.installation_id = self.id

        # Auto-generate Digital Solar Passport upon verified completion
        if not self.passport_id:
            passport_vals = {
                'partner_id': self.partner_id.id,
                'installation_id': self.id,
                'system_type': self.survey_id.system_type if self.survey_id else 'on_grid',
                'commissioning_date': fields.Date.context_today(self),
                'company_id': self.company_id.id,
                'state': 'active',
            }
            passport = self.env['solar.passport'].create(passport_vals)
            self.passport_id = passport.id

            for picking in self.picking_ids:
                for line in picking.move_line_ids.filtered(lambda l: l.lot_id):
                    lot = line.lot_id
                    warranty = self.env['solar.warranty.record'].search([('lot_id', '=', lot.id)], limit=1)
                    comp_type = lot.product_id.solar_component_type or 'inverter'
                    self.env['solar.passport.component'].create({
                        'passport_id': passport.id,
                        'product_id': lot.product_id.id,
                        'component_type': comp_type,
                        'lot_id': lot.id,
                        'warranty_id': warranty.id if warranty else False,
                        'installation_date': fields.Date.context_today(self),
                    })
            self.message_post(body=_(
                "Digital Solar Passport %s generated automatically with verified component registry."
            ) % passport.name)

        self.message_post(body=_(
            "Installation successfully commissioned and marked Completed! "
            "System Output: %s kW (Result: %s). Acceptance signature recorded for %s."
        ) % (
            self.test_generation_kw,
            dict(self._fields['test_result'].selection).get(self.test_result, ''),
            self.customer_signed_by
        ))

    def action_view_passport(self):
        """Smart button action to view the Digital Solar Passport."""
        self.ensure_one()
        if not self.passport_id:
            raise UserError(_("No Digital Solar Passport has been issued for this installation yet."))
        return {
            'name': _('Digital Solar Passport %s', self.passport_id.name),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.passport',
            'res_id': self.passport_id.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        """Cancel installation job."""
        self.ensure_one()
        self.state = 'cancelled'

    def action_view_pickings(self):
        """Smart button action to view delivery pickings linked to this installation."""
        self.ensure_one()
        return {
            'name': _('Delivery Pickings for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('installation_id', '=', self.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_installation_id': self.id,
            },
        }

    def action_view_invoices(self):
        """Smart button action to view customer invoices linked to this installation."""
        self.ensure_one()
        invoices = self.invoice_ids | self.sale_order_id.invoice_ids.filtered(lambda inv: inv.move_type in ('out_invoice', 'out_refund'))
        return {
            'name': _('Customer Invoices for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {
                'default_move_type': 'out_invoice',
                'default_partner_id': self.partner_id.id,
                'default_installation_id': self.id,
                'default_solar_sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
            },
        }

    def action_view_expenses(self):
        """Smart button action to view direct project expenses (vendor bills) linked to this installation."""
        self.ensure_one()
        return {
            'name': _('Direct Project Expenses for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('installation_id', '=', self.id), ('move_type', 'in', ('in_invoice', 'in_refund'))],
            'context': {
                'default_move_type': 'in_invoice',
                'default_installation_id': self.id,
                'default_solar_expense_type': 'freight',
            },
        }

    def action_record_project_expense(self):
        """Action to immediately record a direct project expense bill for this installation."""
        self.ensure_one()
        return {
            'name': _('Record Project Expense for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_move_type': 'in_invoice',
                'default_installation_id': self.id,
                'default_solar_expense_type': 'freight',
            },
        }

    def action_recompute_financials(self):
        """Force recalculation of project financials and log audit summary to Chatter."""
        self.ensure_one()
        self._compute_project_financials()
        self.message_post(body=_(
            "Project Financials Recomputed (DEC-007):\n"
            "- Invoiced Revenue: %s\n"
            "- Material COGS: %s (Gross Margin: %s / %s%%)\n"
            "- Technician Labor Cost: %s (%s hrs @ %s/hr x %s tech)\n"
            "- Attributable Direct Expenses: %s (Freight: %s, Permits: %s, Inspection: %s, Others: %s)\n"
            "- Total Direct Cost: %s\n"
            "- Contribution Profit: %s (Margin: %s%%, Health: %s)"
        ) % (
            self.currency_id.format(self.revenue_invoiced),
            self.currency_id.format(self.cost_materials),
            self.currency_id.format(self.gross_margin),
            self.gross_margin_pct,
            self.currency_id.format(self.cost_technician_labor),
            self.duration_hours,
            self.technician_hourly_rate,
            self.num_technicians,
            self.currency_id.format(self.cost_direct_expenses),
            self.currency_id.format(self.cost_freight),
            self.currency_id.format(self.cost_permits),
            self.currency_id.format(self.cost_inspection),
            self.currency_id.format(self.cost_other_expenses),
            self.currency_id.format(self.cost_total_direct),
            self.currency_id.format(self.contribution_profit),
            self.contribution_margin_pct,
            dict(self._fields['profitability_status'].selection).get(self.profitability_status, '')
        ))
        return True

    def action_view_subsidies(self):
        """Smart button action to view linked subsidy cases."""
        self.ensure_one()
        return {
            'name': _('Subsidy Cases for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.subsidy.case',
            'view_mode': 'list,form',
            'domain': [('installation_id', '=', self.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
                'default_installation_id': self.id,
            },
        }
