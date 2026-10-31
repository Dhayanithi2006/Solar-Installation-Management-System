# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestSolarInstallation(TransactionCase):
    """Test Scenario 4 rooftop installation worksheet, timestamps, power generation test, and customer signature."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Muthukumar S',
            'phone': '+91 95555 44444',
            'email': 'muthu@example.com',
            'street': '44 Temple Road',
            'city': 'Madurai',
        })

        cls.lead_tech = cls.env['res.users'].create({
            'name': 'Senior Installation Tech',
            'login': 'lead_tech_muthu',
            'email': 'leadtech@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_installer').id])],
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
            'advance_payment_policy': 'none',
        })

        cls.installation = cls.env['solar.installation'].create({
            'partner_id': cls.customer.id,
            'sale_order_id': cls.sale_order.id,
            'lead_technician_id': cls.lead_tech.id,
            'installed_capacity_kw': 3.0,
            'state': 'scheduled',
        })

    def test_01_work_start_and_duration_calculation(self):
        """Technician commences work, timestamps are recorded, and duration computes accurately."""
        self.installation.action_start_work()
        self.assertEqual(self.installation.state, 'in_progress')
        self.assertTrue(self.installation.actual_start)

        # Simulate 4.5 hours of rooftop installation work
        start_time = datetime(2026, 11, 1, 9, 0, 0)
        finish_time = datetime(2026, 11, 1, 13, 30, 0)
        self.installation.write({
            'actual_start': start_time,
            'actual_finish': finish_time,
        })
        self.assertEqual(self.installation.duration_hours, 4.5)

    def test_02_completion_blocked_if_power_test_missing(self):
        """Commissioning and completion must fail if power generation test is unconfirmed or zero."""
        self.installation.state = 'in_progress'
        self.installation.write({
            'generation_confirmed': False,
            'test_generation_kw': 0.0,
            'customer_signature': b'sample_sig_data',
            'installation_photo_array': b'sample_photo_data',
        })

        with self.assertRaises(ValidationError):
            self.installation.action_complete()

    def test_03_completion_blocked_if_signature_missing(self):
        """Commissioning and completion must fail if customer acceptance signature is not captured."""
        self.installation.state = 'in_progress'
        self.installation.write({
            'generation_confirmed': True,
            'test_generation_kw': 2.9,
            'test_dc_voltage': 380.0,
            'installation_photo_array': b'sample_photo_data',
            'customer_signature': False,  # Missing signature!
        })

        with self.assertRaises(ValidationError):
            self.installation.action_complete()

    def test_04_successful_commissioning_and_completion(self):
        """With generation confirmed, photo evidence, and customer signature, job marks as completed."""
        self.installation.state = 'in_progress'
        self.installation.write({
            'actual_start': datetime.now() - timedelta(hours=5),
            'test_dc_voltage': 380.0,
            'test_ac_voltage': 230.0,
            'test_generation_kw': 2.85,
            'generation_confirmed': True,
            'test_result': 'passed',
            'gps_latitude': 13.0827,
            'gps_longitude': 80.2707,
            'installation_photo_array': b'sample_array_photo_bytes',
            'installation_photo_inverter': b'sample_inverter_photo_bytes',
            'customer_signature': b'customer_signature_bytes_base64',
            'customer_signed_by': 'Muthukumar S',
        })

        self.installation.action_complete()

        self.assertEqual(self.installation.state, 'completed')
        self.assertTrue(self.installation.actual_finish)
        self.assertTrue(self.installation.customer_signed_date)
        self.assertEqual(self.installation.customer_signed_by, 'Muthukumar S')

        # Verify completion message logged in chatter
        messages = self.installation.message_ids.mapped('body')
        self.assertTrue(any('successfully commissioned and marked Completed' in msg for msg in messages))


    def test_05_completion_blocked_if_voltages_zero(self):
        """Commissioning must fail if DC or AC voltage is 0 or negative."""
        self.installation.state = 'in_progress'
        self.installation.write({
            'generation_confirmed': True,
            'test_generation_kw': 2.9,
            'test_dc_voltage': 0.0,  # Zero DC voltage
            'test_ac_voltage': 230.0,
            'gps_latitude': 13.0827,
            'gps_longitude': 80.2707,
            'customer_signature': b'sig',
            'installation_photo_array': b'photo',
        })
        with self.assertRaises(ValidationError):
            self.installation.action_complete()

    def test_06_completion_blocked_if_technician_missing(self):
        """Commissioning must fail if no lead technician or crew is assigned."""
        self.installation.lead_technician_id = False
        self.installation.technician_ids = [(5, 0, 0)]
        self.installation.state = 'in_progress'
        self.installation.write({
            'generation_confirmed': True,
            'test_generation_kw': 2.9,
            'test_dc_voltage': 380.0,
            'test_ac_voltage': 230.0,
            'gps_latitude': 13.0827,
            'gps_longitude': 80.2707,
            'customer_signature': b'sig',
            'installation_photo_array': b'photo',
        })
        with self.assertRaises(ValidationError):
            self.installation.action_complete()
        # Restore lead tech
        self.installation.lead_technician_id = self.lead_tech.id

    def test_07_completion_blocked_if_gps_missing(self):
        """Commissioning must fail if mandatory GPS coordinates are missing."""
        self.installation.state = 'in_progress'
        self.installation.write({
            'generation_confirmed': True,
            'test_generation_kw': 2.9,
            'test_dc_voltage': 380.0,
            'test_ac_voltage': 230.0,
            'gps_latitude': 0.0,
            'gps_longitude': 0.0,
            'gps_required': True,
            'customer_signature': b'sig',
            'installation_photo_array': b'photo',
        })
        with self.assertRaises(ValidationError):
            self.installation.action_complete()
