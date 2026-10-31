# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestSolarProcurement(TransactionCase):
    """Test solar vendor catalogues, purchase orders, and project-attributable procurement."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier_apex = cls.env.ref('solar_management.supplier_apex_inverters')
        cls.supplier_evergreen = cls.env.ref('solar_management.supplier_evergreen_panels')
        cls.product_inverter = cls.env.ref('solar_management.product_solar_inverter_3kw')
        cls.product_panel = cls.env.ref('solar_management.product_solar_panel_540w')

        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Ganesh V',
            'phone': '+91 91234 56789',
            'email': 'ganesh@example.com',
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_customer.id,
            'advance_payment_policy': 'none',
        })

        cls.installation = cls.env['solar.installation'].create({
            'partner_id': cls.partner_customer.id,
            'sale_order_id': cls.sale_order.id,
        })

    def test_01_supplierinfo_linkage(self):
        """Verify products have active vendor pricing catalogues configured."""
        supplierinfo_inverter = self.env['product.supplierinfo'].search([
            ('product_id', '=', self.product_inverter.id),
            ('partner_id', '=', self.supplier_apex.id),
        ], limit=1)
        self.assertTrue(supplierinfo_inverter)
        self.assertEqual(supplierinfo_inverter.price, 25000.0)

        supplierinfo_panel = self.env['product.supplierinfo'].search([
            ('product_id', '=', self.product_panel.id),
            ('partner_id', '=', self.supplier_evergreen.id),
        ], limit=1)
        self.assertTrue(supplierinfo_panel)
        self.assertEqual(supplierinfo_panel.price, 10500.0)

    def test_02_stock_replenishment_purchase_order(self):
        """Verify stock replenishment purchase order computes solar flag and confirms cleanly."""
        po = self.env['purchase.order'].create({
            'partner_id': self.supplier_apex.id,
            'procurement_type': 'stock',
            'component_category': 'inverter',
            'total_landed_cost_estimated': 1500.0,
            'order_line': [(0, 0, {
                'product_id': self.product_inverter.id,
                'product_qty': 5.0,
                'price_unit': 25000.0,
                'name': self.product_inverter.name,
            })],
        })

        self.assertTrue(po.is_solar_purchase)
        self.assertEqual(po.amount_total, 125000.0)

        po.button_confirm()
        self.assertEqual(po.state, 'purchase')

    def test_03_project_specific_procurement_notification(self):
        """Verify direct project procurement logs notifications on linked sales order and installation."""
        po = self.env['purchase.order'].create({
            'partner_id': self.supplier_evergreen.id,
            'procurement_type': 'project',
            'component_category': 'panel',
            'sale_order_id': self.sale_order.id,
            'installation_id': self.installation.id,
            'total_landed_cost_estimated': 3200.0,
            'order_line': [(0, 0, {
                'product_id': self.product_panel.id,
                'product_qty': 6.0,
                'price_unit': 10500.0,
                'name': self.product_panel.name,
            })],
        })

        self.assertTrue(po.is_solar_purchase)
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')

        # Check notification posted to sale order
        sale_messages = self.sale_order.message_ids.mapped('body')
        self.assertTrue(any(po.name in msg for msg in sale_messages))

        # Check notification posted to installation
        inst_messages = self.installation.message_ids.mapped('body')
        self.assertTrue(any(po.name in msg for msg in inst_messages))

