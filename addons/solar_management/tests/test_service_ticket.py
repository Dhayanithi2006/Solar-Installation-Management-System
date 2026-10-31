# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestServiceTicket(TransactionCase):
    """Test Scenario 5 customer breakdown ticket intake, serial/warranty lookup, and customer confirmation closure gate."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Naveen Prakash',
            'phone': '+91 98888 77777',
            'email': 'naveen@example.com',
            'street': '12 Boat Club Road',
            'city': 'Chennai',
        })

        cls.service_tech = cls.env['res.users'].create({
            'name': 'Service Repair Technician',
            'login': 'service_tech_naveen',
            'email': 'servicetech@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_service').id])],
        })

        cls.product_inverter = cls.env.ref('solar_management.product_solar_inverter_3kw')
        cls.rule_2y = cls.env.ref('solar_management.warranty_rule_solar_inverter_2y')

        cls.active_lot = cls.env['stock.lot'].create({
            'name': 'INV-ACTIVE-CLAIM-001',
            'product_id': cls.product_inverter.id,
            'company_id': cls.env.company.id,
            'customer_id': cls.customer.id,
        })

        cls.active_warranty = cls.env['solar.warranty.record'].create({
            'lot_id': cls.active_lot.id,
            'product_id': cls.product_inverter.id,
            'partner_id': cls.customer.id,
            'rule_id': cls.rule_2y.id,
            'warranty_start': '2025-06-01',
            'warranty_end': '2027-06-01',
            'state': 'active',
        })

        cls.expired_lot = cls.env['stock.lot'].create({
            'name': 'INV-EXPIRED-CLAIM-002',
            'product_id': cls.product_inverter.id,
            'company_id': cls.env.company.id,
            'customer_id': cls.customer.id,
        })

        cls.expired_warranty = cls.env['solar.warranty.record'].create({
            'lot_id': cls.expired_lot.id,
            'product_id': cls.product_inverter.id,
            'partner_id': cls.customer.id,
            'rule_id': cls.rule_2y.id,
            'warranty_start': '2023-01-01',
            'warranty_end': '2025-01-01',
            'state': 'expired',
        })

    def test_01_active_warranty_serial_lookup(self):
        """Ticket automatically identifies active warranty for serial and sets ₹0 covered status."""
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.customer.id,
            'lot_id': self.active_lot.id,
            'fault_category': 'inverter_fault',
            'reported_error_code': 'ERR-F04',
            'issue_description': 'System halted during heavy rain, red LED flashing.',
        })

        self.assertTrue(ticket.warranty_covered)
        self.assertEqual(ticket.warranty_coverage_status, 'covered')
        self.assertEqual(ticket.warranty_id.id, self.active_warranty.id)
        self.assertEqual(ticket.product_id.id, self.product_inverter.id)

    def test_02_expired_warranty_serial_lookup(self):
        """Ticket accurately identifies expired warranty and tags ticket as chargeable customer repair."""
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.customer.id,
            'lot_id': self.expired_lot.id,
            'fault_category': 'inverter_fault',
            'reported_error_code': 'E02',
        })

        self.assertFalse(ticket.warranty_covered)
        self.assertEqual(ticket.warranty_coverage_status, 'out_of_warranty')

    def test_03_closure_blocked_without_customer_confirmation(self):
        """Ticket closure must strictly fail if customer confirmation is not captured."""
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.customer.id,
            'lot_id': self.active_lot.id,
            'fault_category': 'inverter_fault',
            'state': 'resolved',
        })

        with self.assertRaises(ValidationError):
            ticket.action_close()

    def test_04_successful_closure_with_customer_confirmation(self):
        """Recording customer confirmation unlocks ticket closure."""
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.customer.id,
            'lot_id': self.active_lot.id,
            'fault_category': 'inverter_fault',
            'technician_id': self.service_tech.id,
            'state': 'in_progress',
        })

        ticket.action_mark_resolved()
        self.assertEqual(ticket.state, 'resolved')

        # Customer confirms restoration
        ticket.customer_feedback = 'excellent'
        ticket.customer_confirmation_notes = 'Inverter replaced on site, generating 2.8 kW normally.'
        ticket.action_customer_confirm()

        self.assertTrue(ticket.customer_confirmed_resolution)
        self.assertTrue(ticket.resolution_date)

        # Close ticket
        ticket.action_close()
        self.assertEqual(ticket.state, 'closed')


    def test_04_mismatched_customer_serial_rejected(self):
        """Raising a service ticket for a serial belonging to another customer must fail."""
        other_customer = self.env['res.partner'].create({
            'name': 'Other Customer',
        })
        other_lot = self.env['stock.lot'].create({
            'name': 'INV-OTHER-009',
            'product_id': self.product_inverter.id,
            'company_id': self.env.company.id,
            'customer_id': other_customer.id,
        })

        with self.assertRaises(ValidationError):
            self.env['solar.service.ticket'].create({
                'partner_id': self.customer.id,
                'lot_id': other_lot.id,
                'product_id': self.product_inverter.id,
                'fault_category': 'inverter_fault',
            })

    def test_05_duplicate_repair_order_rejected(self):
        """Creating duplicate repair order on same service ticket must be blocked."""
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.customer.id,
            'lot_id': self.active_lot.id,
            'product_id': self.product_inverter.id,
            'fault_category': 'inverter_fault',
        })
        ticket.action_create_repair_order()
        self.assertTrue(ticket.repair_id)

        with self.assertRaises(UserError):
            ticket.action_create_repair_order()
