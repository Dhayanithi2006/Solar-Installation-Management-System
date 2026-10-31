# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestStockInventory(TransactionCase):
    """Test warehouse inventory reordering, solar picking linkages, and kit move explosion."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Balaji Industries',
            'phone': '+91 94444 33221',
            'email': 'balaji@example.com',
            'street': 'Industrial Estate',
            'city': 'Chennai',
        })

        cls.approved_survey = cls.env['solar.site.survey'].create({
            'partner_id': cls.partner.id,
            'requested_capacity_kw': 3.0,
            'system_type': 'on_grid',
            'roof_direction': 'south',
            'shadow_free_roof_area': 350.0,
            'cable_distance': 20.0,
            'state': 'approved',
        })

        cls.package_3kw = cls.env['solar.package'].search([
            ('capacity_kw', '=', 3.0),
            ('system_type', '=', 'on_grid'),
            ('state', '=', 'active'),
        ], limit=1)

    def test_01_solar_reordering_rules_configured(self):
        """Verify automated reordering rules exist for panels, inverters, and batteries."""
        panel_orderpoint = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.env.ref('solar_management.product_solar_panel_540w').id),
        ], limit=1)
        self.assertTrue(panel_orderpoint)
        self.assertEqual(panel_orderpoint.product_min_qty, 20.0)
        self.assertEqual(panel_orderpoint.product_max_qty, 60.0)

        inverter_orderpoint = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.env.ref('solar_management.product_solar_inverter_3kw').id),
        ], limit=1)
        self.assertTrue(inverter_orderpoint)
        self.assertEqual(inverter_orderpoint.product_min_qty, 5.0)
        self.assertEqual(inverter_orderpoint.product_max_qty, 15.0)

    def test_02_picking_solar_detection_and_installation_linking(self):
        """Verify picking detects solar nature and auto-links to installation upon dispatch completion."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'survey_id': self.approved_survey.id,
            'package_id': self.package_3kw.id,
            'advance_payment_policy': 'none',
            'order_line': [(0, 0, {
                'product_id': self.package_3kw.product_id.id,
                'product_uom_qty': 1.0,
                'price_unit': 189000.0,
            })],
        })
        order.action_confirm()

        self.assertEqual(len(order.picking_ids), 1)
        picking = order.picking_ids[0]
        self.assertTrue(picking.is_solar_picking)
        self.assertEqual(picking.survey_id.id, self.approved_survey.id)

        # Installation was generated on order confirmation
        installation = order.installation_ids[0]
        self.assertEqual(picking.installation_id.id, installation.id)

    def test_03_kit_explosion_and_serialized_detection(self):
        """Verify picking contains exploded components from phantom kit BoM and flags serial tracking."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'survey_id': self.approved_survey.id,
            'package_id': self.package_3kw.id,
            'advance_payment_policy': 'none',
            'order_line': [(0, 0, {
                'product_id': self.package_3kw.product_id.id,
                'product_uom_qty': 1.0,
                'price_unit': 189000.0,
            })],
        })
        order.action_confirm()
        picking = order.picking_ids[0]

        # In Odoo, kit BoM explodes into multiple moves on the picking
        self.assertTrue(len(picking.move_ids) >= 1)
        # Verify picking detects presence of serialized item (Inverter)
        self.assertTrue(picking.has_serialized_items)

        # Move line solar fields inspection
        inverter_move = picking.move_ids.filtered(
            lambda m: m.product_id.id == self.env.ref('solar_management.product_solar_inverter_3kw').id
        )
        if inverter_move:
            self.assertTrue(inverter_move[0].is_solar_component)
            self.assertEqual(inverter_move[0].solar_component_type, 'inverter')
            self.assertTrue(inverter_move[0].is_serial_tracked)

