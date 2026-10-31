# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestSolarSaleQuotation(TransactionCase):
    """Test solar quotation generation, package selection, advance payment, and order confirmation handoff."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sales_user = cls.env['res.users'].create({
            'name': 'Test Solar Sales Rep',
            'login': 'sales_rep_test',
            'email': 'sales@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_sales').id])],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Ramesh Sundaram',
            'phone': '+91 98888 11111',
            'email': 'ramesh@example.com',
            'street': '88 Marina View',
            'city': 'Chennai',
        })

        cls.lead = cls.env['crm.lead'].create({
            'name': 'Ramesh Sundaram — 3 kW On-Grid',
            'partner_id': cls.partner.id,
            'contact_name': 'Ramesh Sundaram',
            'phone': '+91 98888 11111',
            'requested_capacity_kw': 3.0,
            'requested_system_type': 'on_grid',
            'subsidy_interest': True,
        })

        cls.approved_survey = cls.env['solar.site.survey'].create({
            'partner_id': cls.partner.id,
            'lead_id': cls.lead.id,
            'requested_capacity_kw': 3.0,
            'system_type': 'on_grid',
            'roof_direction': 'south',
            'roof_tilt': 15.0,
            'shadow_free_roof_area': 350.0,
            'cable_distance': 18.0,
            'roof_structure': 'rcc',
            'shading_analysis': 'no_shade',
            'grid_suitability': 'suitable',
            'state': 'approved',
        })

        cls.package_3kw = cls.env['solar.package'].search([
            ('capacity_kw', '=', 3.0),
            ('system_type', '=', 'on_grid'),
            ('state', '=', 'active'),
        ], limit=1)

    def test_01_quotation_creation_and_package_selection(self):
        """Verify quotation links to approved survey and selecting package adds product lines."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': self.lead.id,
            'survey_id': self.approved_survey.id,
            'package_id': self.package_3kw.id,
        })
        order._onchange_package_id()

        self.assertTrue(order.is_solar_order)
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line[0].product_id.id, self.package_3kw.product_id.id)
        self.assertEqual(order.order_line[0].price_unit, self.package_3kw.sales_price)

    def test_02_advance_payment_calculation_and_recording(self):
        """Verify advance payment calculation, state transitions, and work readiness."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'survey_id': self.approved_survey.id,
            'package_id': self.package_3kw.id,
            'advance_payment_policy': 'percentage',
            'advance_percentage': 20.0,
            'order_line': [(0, 0, {
                'product_id': self.package_3kw.product_id.id,
                'product_uom_qty': 1.0,
                'price_unit': 189000.0,
            })],
        })

        expected_advance = 189000.0 * 0.20  # 37,800.0
        self.assertEqual(order.advance_amount_required, expected_advance)
        self.assertEqual(order.advance_payment_status, 'pending')
        self.assertFalse(order.work_ready)

        # Record advance payment
        payment = order.action_record_advance_payment()
        self.assertEqual(order.advance_amount_paid, expected_advance)
        self.assertEqual(order.advance_payment_status, 'paid')
        self.assertTrue(order.work_ready)
        self.assertTrue(order.advance_payment_ids)
        self.assertEqual(order.advance_payment_id.id, payment.id)

        # Duplicate payment attempt must be rejected
        with self.assertRaises(UserError):
            order.action_record_advance_payment()

    def test_03_confirmation_blocked_if_survey_not_approved(self):
        """Order confirmation must fail if linked survey is not approved."""
        unapproved_survey = self.env['solar.site.survey'].create({
            'partner_id': self.partner.id,
            'requested_capacity_kw': 3.0,
            'state': 'draft',
        })

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'survey_id': unapproved_survey.id,
            'package_id': self.package_3kw.id,
            'advance_payment_policy': 'none',
            'order_line': [(0, 0, {
                'product_id': self.package_3kw.product_id.id,
                'product_uom_qty': 1.0,
                'price_unit': 189000.0,
            })],
        })

        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_04_confirmation_blocked_without_advance_payment(self):
        """Order confirmation must fail for standard sales rep if required advance payment is pending."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'survey_id': self.approved_survey.id,
            'package_id': self.package_3kw.id,
            'advance_payment_policy': 'percentage',
            'advance_percentage': 20.0,
            'order_line': [(0, 0, {
                'product_id': self.package_3kw.product_id.id,
                'product_uom_qty': 1.0,
                'price_unit': 189000.0,
            })],
        })

        with self.assertRaises(ValidationError):
            order.with_user(self.sales_user).action_confirm()

    def test_05_successful_confirmation_and_downstream_handoff(self):
        """Confirmed solar order automatically generates installation job and subsidy case."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': self.lead.id,
            'survey_id': self.approved_survey.id,
            'package_id': self.package_3kw.id,
            'advance_payment_policy': 'percentage',
            'advance_percentage': 20.0,
            'order_line': [(0, 0, {
                'product_id': self.package_3kw.product_id.id,
                'product_uom_qty': 1.0,
                'price_unit': 189000.0,
            })],
        })

        order.action_record_advance_payment()
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertEqual(order.installation_count, 1)

        installation = order.installation_ids[0]
        self.assertEqual(installation.partner_id.id, self.partner.id)
        self.assertEqual(installation.survey_id.id, self.approved_survey.id)
        self.assertEqual(installation.state, 'draft')

        # Verify Subsidy Case auto-generation (lead had subsidy_interest=True)
        self.assertEqual(order.subsidy_count, 1)
        subsidy = order.subsidy_case_ids[0]
        self.assertEqual(subsidy.partner_id.id, self.partner.id)
        self.assertEqual(subsidy.state, 'draft')

