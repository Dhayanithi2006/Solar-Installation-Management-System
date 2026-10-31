# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestWarrantyManagement(TransactionCase):
    """Test Scenario 5 warranty policies, expiration calculation, status determination, and service claim generation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Suresh Menon',
            'phone': '+91 96666 55555',
            'email': 'suresh@example.com',
            'street': '15 Alwarpet Street',
            'city': 'Chennai',
        })

        cls.product_inverter = cls.env.ref('solar_management.product_solar_inverter_3kw')
        cls.product_panel = cls.env.ref('solar_management.product_solar_panel_540w')
        cls.rule_inverter_2y = cls.env.ref('solar_management.warranty_rule_solar_inverter_2y')
        cls.rule_panel_20y = cls.env.ref('solar_management.warranty_rule_solar_panel_20y')

        cls.lot_inverter = cls.env['stock.lot'].create({
            'name': 'INV-TEST-WAR-001',
            'product_id': cls.product_inverter.id,
            'company_id': cls.env.company.id,
            'customer_id': cls.customer.id,
        })

    def test_01_warranty_expiry_date_calculation(self):
        """Verify automatic warranty end date calculation for 2-year inverter and 20-year panel policies."""
        start_date = date(2026, 1, 15)

        # 2-Year Inverter Policy
        warranty_inv = self.env['solar.warranty.record'].create({
            'lot_id': self.lot_inverter.id,
            'product_id': self.product_inverter.id,
            'partner_id': self.customer.id,
            'rule_id': self.rule_inverter_2y.id,
            'warranty_start': start_date,
        })
        self.assertEqual(warranty_inv.warranty_end, date(2028, 1, 15))

        # 20-Year Panel Policy
        lot_panel = self.env['stock.lot'].create({
            'name': 'PANEL-TEST-001',
            'product_id': self.product_panel.id,
            'company_id': self.env.company.id,
        })
        warranty_panel = self.env['solar.warranty.record'].create({
            'lot_id': lot_panel.id,
            'product_id': self.product_panel.id,
            'partner_id': self.customer.id,
            'rule_id': self.rule_panel_20y.id,
            'warranty_start': start_date,
        })
        self.assertEqual(warranty_panel.warranty_end, date(2046, 1, 15))

    def test_02_warranty_status_and_days_remaining(self):
        """Verify days remaining and status transitions (active vs expired)."""
        today = date.today()

        # Active warranty: Started today, expires in 2 years
        active_warranty = self.env['solar.warranty.record'].create({
            'lot_id': self.lot_inverter.id,
            'product_id': self.product_inverter.id,
            'partner_id': self.customer.id,
            'rule_id': self.rule_inverter_2y.id,
            'warranty_start': today,
        })
        self.assertEqual(active_warranty.state, 'active')
        self.assertTrue(active_warranty.is_valid)
        self.assertTrue(active_warranty.days_remaining > 700)

        # Expired warranty: Started 3 years ago
        expired_warranty = self.env['solar.warranty.record'].create({
            'lot_id': self.lot_inverter.id,
            'product_id': self.product_inverter.id,
            'partner_id': self.customer.id,
            'rule_id': self.rule_inverter_2y.id,
            'warranty_start': today - relativedelta(years=3),
        })
        self.assertEqual(expired_warranty.state, 'expired')
        self.assertFalse(expired_warranty.is_valid)
        self.assertEqual(expired_warranty.days_remaining, 0)

    def test_03_warranty_void_and_reactivation(self):
        """Manager can void a warranty for unauthorized customer tampering and re-activate if justified."""
        warranty = self.env['solar.warranty.record'].create({
            'lot_id': self.lot_inverter.id,
            'product_id': self.product_inverter.id,
            'partner_id': self.customer.id,
            'rule_id': self.rule_inverter_2y.id,
            'warranty_start': date.today(),
        })
        self.assertEqual(warranty.state, 'active')

        warranty.action_void_warranty()
        self.assertEqual(warranty.state, 'void')

        warranty.action_reactivate_warranty()
        self.assertEqual(warranty.state, 'active')

    def test_04_action_create_service_ticket_handoff(self):
        """Creating a service ticket from warranty pre-fills equipment, customer, and warranty reference."""
        warranty = self.env['solar.warranty.record'].create({
            'lot_id': self.lot_inverter.id,
            'product_id': self.product_inverter.id,
            'partner_id': self.customer.id,
            'rule_id': self.rule_inverter_2y.id,
            'warranty_start': date.today(),
        })

        action = warranty.action_create_service_ticket()
        self.assertTrue(action)
        self.assertEqual(action.get('res_model'), 'solar.service.ticket')

        ticket = self.env['solar.service.ticket'].browse(action['res_id'])
        self.assertEqual(ticket.partner_id.id, self.customer.id)
        self.assertEqual(ticket.lot_id.id, self.lot_inverter.id)
        self.assertEqual(ticket.product_id.id, self.product_inverter.id)
        self.assertEqual(ticket.warranty_id.id, warranty.id)
        self.assertEqual(warranty.ticket_count, 1)

