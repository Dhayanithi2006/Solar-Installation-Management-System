# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_solar_picking = fields.Boolean(
        string='Is Solar Dispatch',
        compute='_compute_is_solar_picking',
        store=True,
        tracking=True
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Solar Installation Job',
        tracking=True,
        copy=False,
        help='Target rooftop solar installation job receiving this hardware dispatch.'
    )
    survey_id = fields.Many2one(
        'solar.site.survey',
        string='Approved Site Survey',
        related='sale_id.survey_id',
        store=True,
        readonly=True
    )
    has_serialized_items = fields.Boolean(
        string='Contains Serialized Equipment',
        compute='_compute_has_serialized_items',
        store=True
    )
    barcode_scan_input = fields.Char(
        string='Scan Serial Barcode',
        help='Scan or enter serial number barcode here to automatically assign to matching equipment move line.'
    )

    @api.depends('sale_id.is_solar_order', 'installation_id', 'move_ids.product_id')
    def _compute_is_solar_picking(self):
        for picking in self:
            picking.is_solar_picking = bool(
                picking.installation_id or
                (picking.sale_id and picking.sale_id.is_solar_order) or
                any(move.product_id.is_solar_component for move in picking.move_ids)
            )

    @api.depends('move_ids.product_id.tracking')
    def _compute_has_serialized_items(self):
        for picking in self:
            picking.has_serialized_items = any(
                move.product_id.tracking in ('serial', 'lot') for move in picking.move_ids
            )

    def action_scan_serial_barcode(self, barcode=None):
        """Community-compatible barcode scanning helper to rapidly assign serials to move lines."""
        self.ensure_one()
        code = (barcode or self.barcode_scan_input or '').strip()
        if not code:
            raise UserError(_("Please enter or scan a serial number barcode."))

        # 1. Search for existing stock.lot by name
        lot = self.env['stock.lot'].search([('name', '=', code)], limit=1)

        # 2. Identify candidate move lines waiting for a serial
        unassigned_lines = self.move_line_ids.filtered(
            lambda l: l.product_id.tracking == 'serial' and not l.lot_id
        )

        if not unassigned_lines:
            raise UserError(_("No pending serial-tracked equipment line requires serial scanning in this dispatch."))

        target_line = False
        if lot:
            # Find line matching lot's product
            matching_lines = unassigned_lines.filtered(lambda l: l.product_id.id == lot.product_id.id)
            if not matching_lines:
                raise UserError(_("Scanned Serial '%s' belongs to '%s', which has no unassigned line in this dispatch.") % (code, lot.product_id.name))
            target_line = matching_lines[0]
        else:
            # Create lot on the fly for the first unassigned serial move
            target_line = unassigned_lines[0]
            lot = self.env['stock.lot'].create({
                'name': code,
                'product_id': target_line.product_id.id,
                'company_id': self.company_id.id,
            })

        # Check duplicate assignment in this transfer
        if lot.id in self.move_line_ids.mapped('lot_id.id'):
            raise ValidationError(_("Serial '%s' is already assigned to another line in this dispatch.") % code)

        target_line.write({
            'lot_id': lot.id,
            'quantity': 1.0,
        })
        self.barcode_scan_input = False
        self.message_post(body=_(
            "Barcode scan accepted: Serial '%s' assigned to '%s'."
        ) % (lot.name, target_line.product_id.name))
        return True

    def button_validate(self):
        """Scenario 3: Enforce advance payment clearance and mandatory serial scanning before dispatch validation."""
        for picking in self:
            if picking.is_solar_picking:
                # 1. Advance Payment Gate Check
                so = picking.sale_id
                if so and so.is_solar_order:
                    if so.advance_payment_policy != 'none' and so.advance_payment_status not in ('paid', 'not_required'):
                        if not self.env.user.has_group('solar_management.group_solar_manager'):
                            raise ValidationError(_(
                                "Dispatch Validation Blocked (Scenario 2 & 3 Gate):\n"
                                "Material dispatch for order '%s' is prohibited because customer advance "
                                "payment has not been cleared (Required: %s | Status: %s).\n"
                                "Warehouse cannot dispatch equipment until advance payment is registered and posted."
                            ) % (
                                so.name,
                                so.currency_id.format(so.advance_amount_required),
                                dict(so._fields['advance_payment_status'].selection).get(so.advance_payment_status, '')
                            ))

                # 2. Verify every serial-tracked move has valid serial numbers scanned
                for move in picking.move_ids:
                    if move.product_id.tracking == 'serial':
                        move_lines = move.move_line_ids
                        if not move_lines:
                            raise ValidationError(_(
                                "Dispatch Validation Blocked (Scenario 3):\n"
                                "Product '%s' is configured as Serial-Tracked equipment. "
                                "You must scan/enter unique serial numbers before completing dispatch."
                            ) % move.product_id.name)

                        missing_serials = move_lines.filtered(lambda l: not l.lot_id)
                        if missing_serials:
                            raise ValidationError(_(
                                "Dispatch Validation Blocked (Scenario 3):\n"
                                "Missing serial number for %d unit(s) of '%s'. "
                                "Please scan every individual serial number (inverter, battery, or charge controller)."
                            ) % (len(missing_serials), move.product_id.name))

                # 3. Block duplicate serial numbers within the transfer
                scanned_lots = [line.lot_id.id for line in picking.move_line_ids if line.lot_id]
                if len(scanned_lots) != len(set(scanned_lots)):
                    raise ValidationError(_(
                        "Duplicate Serial Assignment Blocked (Scenario 3):\n"
                        "The same serial number was scanned multiple times in this dispatch. "
                        "Each unit must have a distinct, unique serial number."
                    ))

        return super().button_validate()

    def _action_done(self):
        """Scenario 3: Link equipment to customer/installation, activate warranties, and synchronize installation schedule."""
        res = super()._action_done()
        delivery_date = fields.Date.context_today(self)

        for picking in self:
            if picking.is_solar_picking:
                # Auto-link to installation if not yet set
                if not picking.installation_id and picking.sale_id and picking.sale_id.installation_ids:
                    picking.installation_id = picking.sale_id.installation_ids[0].id

                # Link serialized units to customer and installation, activate warranty
                for line in picking.move_line_ids.filtered(lambda l: l.lot_id):
                    lot = line.lot_id
                    lot.write({
                        'customer_id': picking.partner_id.id,
                        'installation_id': picking.installation_id.id if picking.installation_id else False,
                    })

                    # Idempotent warranty activation: prevent duplicate certificates for the same serial
                    existing_warranty = self.env['solar.warranty.record'].search([
                        ('lot_id', '=', lot.id),
                    ], limit=1)

                    if existing_warranty:
                        update_vals = {}
                        if not existing_warranty.picking_id:
                            update_vals['picking_id'] = picking.id
                        if not existing_warranty.installation_id and picking.installation_id:
                            update_vals['installation_id'] = picking.installation_id.id
                        if update_vals:
                            existing_warranty.write(update_vals)
                    else:
                        # Find matching warranty rule
                        rule = (
                            lot.product_id.default_warranty_rule_id or
                            self.env['solar.warranty.rule'].search([
                                '|',
                                ('product_id', '=', lot.product_id.id),
                                ('product_tmpl_id', '=', lot.product_id.product_tmpl_id.id),
                            ], limit=1)
                        )
                        warranty_vals = {
                            'lot_id': lot.id,
                            'product_id': lot.product_id.id,
                            'partner_id': picking.partner_id.id,
                            'picking_id': picking.id,
                            'sale_order_id': picking.sale_id.id if picking.sale_id else False,
                            'installation_id': picking.installation_id.id if picking.installation_id else False,
                            'rule_id': rule.id if rule else False,
                            'warranty_start': delivery_date,
                            'state': 'active',
                        }
                        warranty = self.env['solar.warranty.record'].create(warranty_vals)
                        picking.message_post(body=_(
                            "Warranty Certificate %s automatically activated for serial '%s' (%s) starting %s."
                        ) % (warranty.name, lot.name, lot.product_id.name, delivery_date))

                # Synchronize installation schedule readiness
                if picking.installation_id:
                    if picking.installation_id.state == 'draft':
                        picking.installation_id.state = 'scheduled'
                    picking.installation_id.message_post(body=_(
                        "Delivery Dispatch %s completed. All solar hardware delivered to site. "
                        "Installation status updated to Scheduled."
                    ) % picking.name)

        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_solar_component = fields.Boolean(
        related='product_id.is_solar_component',
        string='Is Solar Hardware',
        readonly=True
    )
    solar_component_type = fields.Selection(
        related='product_id.solar_component_type',
        string='Component Type',
        readonly=True
    )
    is_serial_tracked = fields.Boolean(
        string='Serial Tracking Required',
        compute='_compute_is_serial_tracked',
        store=True
    )

    @api.depends('product_id.tracking')
    def _compute_is_serial_tracked(self):
        for move in self:
            move.is_serial_tracked = (move.product_id.tracking == 'serial')
