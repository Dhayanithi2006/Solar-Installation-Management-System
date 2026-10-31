# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestSerialTracking(TransactionCase):
    """Test Scenario 3 mandatory serial scanning, duplicate blocking, customer linking, and warranty activation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Karthik Raja',
            'phone': '+91 98765 12345',
            'email': 'karthik@example.com',
            'street': '77 Velachery Main Road',
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
        })

        # Serial Lot
        cls.test_lot = cls.env['stock.lot'].create({
            'name': 'INV-TEST-SER-001',
            'product_id': cls.product_inverter.id,
            'company_id': cls.env.company.id,
        })

    def test_01_mandatory_serial_scanning_blocked_if_empty(self):
        """Dispatch validation must fail if serial-tracked equipment has no serial number."""
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

        # Attempt to validate without scanning lot_id
        with self.assertRaises(ValidationError):
            picking.button_validate()

    def test_02_duplicate_serial_assignment_blocked(self):
        """Dispatch validation must block if the same serial is assigned multiple times."""
        picking = self.env['stock.picking'].create({
            'partner_id': self.customer.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'installation_id': self.installation.id,
            'move_ids': [(0, 0, {
                'name': self.product_inverter.name,
                'product_id': self.product_inverter.id,
                'product_uom_qty': 2.0,
                'product_uom': self.product_inverter.uom_id.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()

        move = picking.move_ids[0]
        # Assign same lot to both move lines
        move.move_line_ids.unlink()
        self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.product_inverter.id,
            'product_uom_id': self.product_inverter.uom_id.id,
            'quantity': 1.0,
            'lot_id': self.test_lot.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.product_inverter.id,
            'product_uom_id': self.product_inverter.uom_id.id,
            'quantity': 1.0,
            'lot_id': self.test_lot.id,  # Duplicate!
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })

        with self.assertRaises(ValidationError):
            picking.button_validate()

    def test_03_successful_dispatch_and_warranty_activation(self):
        """Valid serial scan completes dispatch, links to customer/installation, and activates warranty."""
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

        move = picking.move_ids[0]
        move.move_line_ids.unlink()
        self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.product_inverter.id,
            'product_uom_id': self.product_inverter.uom_id.id,
            'quantity': 1.0,
            'lot_id': self.test_lot.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })

        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        # Verify lot customer and installation linking
        self.assertEqual(self.test_lot.customer_id.id, self.customer.id)
        self.assertEqual(self.test_lot.installation_id.id, self.installation.id)

        # Verify automatic warranty activation on delivery date
        self.assertEqual(self.test_lot.warranty_status, 'active')
        self.assertTrue(self.test_lot.warranty_record_id)
        warranty = self.test_lot.warranty_record_id
        self.assertEqual(warranty.partner_id.id, self.customer.id)
        self.assertEqual(warranty.picking_id.id, picking.id)
        self.assertEqual(warranty.state, 'active')

