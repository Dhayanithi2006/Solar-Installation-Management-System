# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_solar_purchase = fields.Boolean(
        string='Is Solar Procurement',
        compute='_compute_is_solar_purchase',
        store=True,
        tracking=True
    )
    procurement_type = fields.Selection([
        ('stock', 'Inventory Replenishment (Stock Reserve)'),
        ('project', 'Direct Installation / Job Procurement'),
    ], string='Procurement Purpose', default='stock', required=True, tracking=True)

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Linked Solar Sales Order',
        tracking=True,
        help='Customer order demanding this procurement.'
    )
    installation_id = fields.Many2one(
        'solar.installation',
        string='Target Installation Job',
        tracking=True,
        help='Target rooftop installation project for which this equipment is procured.'
    )
    component_category = fields.Selection([
        ('panel', 'PV Panels'),
        ('inverter', 'Inverters'),
        ('battery', 'Storage Batteries'),
        ('controller', 'Charge Controllers'),
        ('bos', 'Balance of System & Wiring'),
        ('mixed', 'Mixed Solar Consumables'),
    ], string='Solar Equipment Category', default='mixed', tracking=True)

    total_landed_cost_estimated = fields.Monetary(
        string='Estimated Freight / Inward Cost',
        currency_field='currency_id',
        default=0.0,
        tracking=True,
        help='Estimated logistics, transport and handling charges for profitability tracking.'
    )

    @api.depends('order_line.product_id', 'sale_order_id', 'installation_id')
    def _compute_is_solar_purchase(self):
        for order in self:
            order.is_solar_purchase = bool(
                order.sale_order_id or
                order.installation_id or
                any(line.product_id.is_solar_component for line in order.order_line)
            )

    def button_confirm(self):
        """Confirm purchase order and log notifications to linked sales orders and installations."""
        res = super().button_confirm()
        for order in self:
            if order.is_solar_purchase:
                msg = _("Purchase Order %s for supplier '%s' (Total: %s) has been confirmed.") % (
                    order.name, order.partner_id.name, order.currency_id.format(order.amount_total)
                )
                if order.sale_order_id:
                    order.sale_order_id.message_post(body=msg + _(" Procured for customer order."))
                if order.installation_id:
                    order.installation_id.message_post(body=msg + _(" Hardware procurement initiated for this installation."))
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_solar_component = fields.Boolean(
        string='Is Solar Hardware',
        related='product_id.is_solar_component',
        readonly=True
    )
    solar_component_type = fields.Selection(
        related='product_id.solar_component_type',
        string='Solar Hardware Type',
        readonly=True
    )

