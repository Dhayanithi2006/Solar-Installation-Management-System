# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestBarcodeDispatch(TransactionCase):
    """Test barcode scanning helper, dispatch validation, installation synchronization, and delivery report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Lakshmi Narayanan',
            'phone': '+91 97777 88888',
            'email': 'lakshmi@example.com',
            'street': '23 Greenways Road',
            'city': 'Chennai',
        })

        cls.product_inverter = cls.env.ref('solar_management.product_solar_inverter_3kw')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.picking_type_out = cls.env.ref('stock.picking_type_out')

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
            'advance_payment_policy': 'none',
        })

        cls.installation = cls.env['solar.installation'].create({
            'partner_id': cls.customer.id,
            'sale_order_id': cls.sale_order.id,
            'state': 'draft',
        })

    def test_01_barcode_scan_helper_assigns_serial(self):
        """Barcode scanning helper automatically finds matching unassigned line and assigns serial."""
        picking = self.env['stock.picking'].create({
            'partner_id': self.customer.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'installation_id': self.installation.id,
            'move_ids': [(0, 0, {
                'name': self.product_inverter.name,
                'product_id': self.product_inverter.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product_inverter.uom_id.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()

        # Call barcode scan helper with demo inverter serial
        picking.action_scan_serial_barcode('INV-DEMO-001')

        # Verify lot was assigned to move line
        move_line = picking.move_line_ids[0]
        self.assertTrue(move_line.lot_id)
        self.assertEqual(move_line.lot_id.name, 'INV-DEMO-001')
        self.assertEqual(move_line.quantity, 1.0)

    def test_02_dispatch_completion_synchronizes_installation(self):
        """Validating dispatch synchronizes installation status to scheduled and sets hardware_delivered."""
        self.assertFalse(self.installation.hardware_delivered)
        self.assertEqual(self.installation.state, 'draft')

        picking = self.env['stock.picking'].create({
            'partner_id': self.customer.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'installation_id': self.installation.id,
            'move_ids': [(0, 0, {
                'name': self.product_inverter.name,
                'product_id': self.product_inverter.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product_inverter.uom_id.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()

        # Assign serial and validate
        picking.action_scan_serial_barcode('INV-SCAN-TEST-002')
        picking.button_validate()

        self.assertEqual(picking.state, 'done')
        self.assertTrue(self.installation.hardware_delivered)
        self.assertEqual(self.installation.state, 'scheduled')

    def test_03_delivery_slip_report_action_available(self):
        """Verify the solar delivery slip report action is properly registered."""
        report = self.env.ref('solar_management.action_report_solar_delivery_slip')
        self.assertTrue(report)
        self.assertEqual(report.model, 'stock.picking')
        self.assertEqual(report.report_type, 'qweb-pdf')


    def test_04_dispatch_blocked_without_advance_payment(self):
        """Warehouse cannot validate dispatch if required advance payment is pending."""
        order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'advance_payment_policy': 'percentage',
            'advance_percentage': 20.0,
            'order_line': [(0, 0, {
                'product_id': self.product_inverter.id,
                'product_uom_qty': 1.0,
                'price_unit': 45000.0,
            })],
        })

        inst = self.env['solar.installation'].create({
            'partner_id': self.customer.id,
            'sale_order_id': order.id,
            'state': 'draft',
        })

        picking = self.env['stock.picking'].create({
            'partner_id': self.customer.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'installation_id': inst.id,
            'sale_id': order.id,
            'move_ids': [(0, 0, {
                'name': self.product_inverter.name,
                'product_id': self.product_inverter.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product_inverter.uom_id.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()
        picking.action_scan_serial_barcode('INV-GATE-TEST-003')

        # Validation must be blocked because advance payment is pending
        with self.assertRaises(ValidationError):
            picking.button_validate()

        # Once advance payment is cleared, dispatch succeeds
        order.action_record_advance_payment()
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
