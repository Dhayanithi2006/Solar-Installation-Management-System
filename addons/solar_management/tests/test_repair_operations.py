# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestRepairOperations(TransactionCase):
    """Test Scenario 5 repair operations, automated ₹0 warranty decision, and out-of-warranty billing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Bala Subramanian',
            'phone': '+91 94444 88888',
            'email': 'bala@example.com',
            'street': '99 T Nagar',
            'city': 'Chennai',
        })

        cls.product_inverter = cls.env.ref('solar_management.product_solar_inverter_3kw')
        cls.rule_inverter = cls.env.ref('solar_management.warranty_rule_solar_inverter_2y')

        cls.covered_lot = cls.env['stock.lot'].create({
            'name': 'INV-COVERED-REP-001',
            'product_id': cls.product_inverter.id,
            'company_id': cls.env.company.id,
            'customer_id': cls.customer.id,
        })

        cls.active_warranty = cls.env['solar.warranty.record'].create({
            'lot_id': cls.covered_lot.id,
            'product_id': cls.product_inverter.id,
            'partner_id': cls.customer.id,
            'rule_id': cls.rule_inverter.id,
            'warranty_start': '2025-05-01',
            'warranty_end': '2027-05-01',
            'state': 'active',
        })

        cls.expired_lot = cls.env['stock.lot'].create({
            'name': 'INV-EXPIRED-REP-002',
            'product_id': cls.product_inverter.id,
            'company_id': cls.env.company.id,
            'customer_id': cls.customer.id,
        })

        cls.expired_warranty = cls.env['solar.warranty.record'].create({
            'lot_id': cls.expired_lot.id,
            'product_id': cls.product_inverter.id,
            'partner_id': cls.customer.id,
            'rule_id': cls.rule_inverter.id,
            'warranty_start': '2022-01-01',
            'warranty_end': '2024-01-01',
            'state': 'expired',
        })

    def test_01_create_repair_order_from_active_warranty_ticket(self):
        """Repair generated from active warranty ticket enforces ₹0 covered billing."""
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.customer.id,
            'lot_id': self.covered_lot.id,
            'product_id': self.product_inverter.id,
            'fault_category': 'inverter_fault',
            'reported_error_code': 'ERR-F04',
            'state': 'assigned',
        })

        action = ticket.action_create_repair_order()
        self.assertTrue(action)
        self.assertEqual(action.get('res_model'), 'repair.order')
        self.assertEqual(ticket.repair_count, 1)

        repair = self.env['repair.order'].browse(action['res_id'])
        self.assertEqual(repair.ticket_id.id, ticket.id)
        self.assertEqual(repair.lot_id.id, self.covered_lot.id)
        self.assertTrue(repair.is_solar_repair)
        self.assertTrue(repair.is_covered_repair)
        self.assertEqual(repair.warranty_coverage_status, 'covered')
        self.assertIn('₹0 WARRANTY COVERED REPAIR', repair.warranty_notes)

    def test_02_create_repair_order_from_out_of_warranty_ticket(self):
        """Repair generated from expired warranty ticket enforces chargeable customer billing."""
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.customer.id,
            'lot_id': self.expired_lot.id,
            'product_id': self.product_inverter.id,
            'fault_category': 'inverter_fault',
            'reported_error_code': 'ERR-PWR',
            'state': 'assigned',
        })

        action = ticket.action_create_repair_order()
        repair = self.env['repair.order'].browse(action['res_id'])

        self.assertTrue(repair.is_solar_repair)
        self.assertFalse(repair.is_covered_repair)
        self.assertEqual(repair.warranty_coverage_status, 'out_of_warranty')
        self.assertIn('CHARGEABLE CUSTOMER REPAIR', repair.warranty_notes)

