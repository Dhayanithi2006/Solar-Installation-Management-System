# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    installation_id = fields.Many2one(
        'solar.installation',
        string='Solar Installation Job',
        tracking=True,
        copy=False,
        ondelete='set null',
        help='Target rooftop solar installation job receiving revenue or incurring direct project costs.'
    )
    is_solar_invoice = fields.Boolean(
        string='Is Solar Customer Invoice',
        compute='_compute_is_solar_move',
        store=True,
        tracking=True
    )
    is_solar_expense = fields.Boolean(
        string='Is Solar Project Expense',
        compute='_compute_is_solar_move',
        store=True,
        tracking=True
    )
    solar_expense_type = fields.Selection([
        ('freight', 'Freight & Logistics Transport'),
        ('permit', 'Net-Metering & DISCOM Grid Permits'),
        ('inspection', 'Electrical Safety & CEIG Inspection'),
        ('consumables', 'Mounting Hardware & Consumables'),
        ('liaison', 'DISCOM Liaison & Documentation'),
        ('other', 'Other Direct Project Expense'),
    ], string='Project Expense Category', tracking=True, help='Attributable direct project expense category for DEC-007 contribution costing.')

    solar_sale_order_id = fields.Many2one(
        'sale.order',
        string='Linked Solar Sale Order',
        compute='_compute_solar_sale_order',
        store=True,
        readonly=False,
        tracking=True
    )

    @api.depends('installation_id', 'move_type', 'solar_expense_type', 'line_ids.sale_line_ids.order_id.is_solar_order')
    def _compute_is_solar_move(self):
        for move in self:
            is_solar_so = any(line.sale_line_ids.order_id.is_solar_order for line in move.line_ids)
            has_solar_inst = bool(move.installation_id)
            if move.move_type in ('out_invoice', 'out_refund'):
                move.is_solar_invoice = has_solar_inst or is_solar_so
                move.is_solar_expense = False
            elif move.move_type in ('in_invoice', 'in_refund'):
                move.is_solar_invoice = False
                move.is_solar_expense = has_solar_inst or bool(move.solar_expense_type)
            else:
                move.is_solar_invoice = False
                move.is_solar_expense = False

    @api.depends('line_ids.sale_line_ids.order_id', 'installation_id.sale_order_id')
    def _compute_solar_sale_order(self):
        for move in self:
            if move.installation_id and move.installation_id.sale_order_id:
                move.solar_sale_order_id = move.installation_id.sale_order_id
            else:
                so = move.line_ids.sale_line_ids.order_id
                if so:
                    move.solar_sale_order_id = so[0]
                elif not move.solar_sale_order_id:
                    move.solar_sale_order_id = False

    @api.onchange('solar_sale_order_id')
    def _onchange_solar_sale_order_id(self):
        if self.solar_sale_order_id and self.solar_sale_order_id.installation_ids:
            self.installation_id = self.solar_sale_order_id.installation_ids[0].id

    def action_view_solar_installation(self):
        self.ensure_one()
        if not self.installation_id:
            raise UserError(_("No Solar Installation Job linked to this record."))
        return {
            'name': _('Solar Installation %s', self.installation_id.name),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.installation',
            'view_mode': 'form',
            'res_id': self.installation_id.id,
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    installation_id = fields.Many2one(
        'solar.installation',
        string='Solar Installation Job',
        related='move_id.installation_id',
        store=True,
        readonly=True
    )
    solar_expense_type = fields.Selection(
        related='move_id.solar_expense_type',
        string='Solar Expense Category',
        store=True,
        readonly=True
    )

