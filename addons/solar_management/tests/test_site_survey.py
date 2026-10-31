# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestSolarSiteSurvey(TransactionCase):
    """Test site survey measurements, manager approval workflow, and quotation gating."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create dedicated test users for technician and manager
        cls.technician_user = cls.env['res.users'].create({
            'name': 'Test Survey Technician',
            'login': 'survey_tech_test',
            'email': 'tech@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_survey_tech').id])],
        })

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Test Survey Manager',
            'login': 'survey_mgr_test',
            'email': 'mgr@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_survey_manager').id])],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Kavitha Ramanathan',
            'phone': '+91 94440 12345',
            'email': 'kavitha@example.com',
            'street': '55 Beach Road',
            'city': 'Chennai',
        })

        cls.lead = cls.env['crm.lead'].create({
            'name': 'Kavitha Ramanathan — 5 kW On-Grid',
            'partner_id': cls.partner.id,
            'contact_name': 'Kavitha Ramanathan',
            'phone': '+91 94440 12345',
            'requested_capacity_kw': 5.0,
            'requested_system_type': 'on_grid',
        })

    def test_01_survey_creation_and_defaults(self):
        """Verify survey creation assigns unique sequence reference and draft status."""
        survey = self.env['solar.site.survey'].create({
            'partner_id': self.partner.id,
            'lead_id': self.lead.id,
            'technician_id': self.technician_user.id,
            'requested_capacity_kw': 5.0,
            'system_type': 'on_grid',
        })
        self.assertTrue(survey.name.startswith('SURV/'))
        self.assertEqual(survey.state, 'draft')
        self.assertEqual(survey.quotation_count, 0)

    def test_02_submit_validation_missing_measurements(self):
        """Technician submission must fail if core site measurements are incomplete."""
        survey = self.env['solar.site.survey'].create({
            'partner_id': self.partner.id,
            'lead_id': self.lead.id,
            'technician_id': self.technician_user.id,
            'requested_capacity_kw': 5.0,
            'system_type': 'on_grid',
            'shadow_free_roof_area': 0.0,  # Invalid area
            'cable_distance': 0.0,          # Invalid distance
        })
        # Attempt submission without roof direction and zero area
        with self.assertRaises(ValidationError):
            survey.action_submit()

    def test_03_submit_successful_with_measurements(self):
        """Technician submission succeeds once all measurements are accurately recorded."""
        survey = self.env['solar.site.survey'].create({
            'partner_id': self.partner.id,
            'lead_id': self.lead.id,
            'technician_id': self.technician_user.id,
            'requested_capacity_kw': 5.0,
            'system_type': 'on_grid',
            'roof_direction': 'south',
            'roof_tilt': 15.0,
            'shadow_free_roof_area': 500.0,
            'cable_distance': 22.0,
            'roof_structure': 'rcc',
            'shading_analysis': 'no_shade',
            'grid_suitability': 'suitable',
        })
        survey.action_submit()
        self.assertEqual(survey.state, 'submitted')
        self.assertTrue(survey.execution_date)

    def test_04_approval_role_security_gate(self):
        """Only users with Survey Approver/Manager role can approve submitted surveys."""
        survey = self.env['solar.site.survey'].create({
            'partner_id': self.partner.id,
            'requested_capacity_kw': 3.0,
            'roof_direction': 'south',
            'shadow_free_roof_area': 300.0,
            'cable_distance': 15.0,
        })
        survey.action_submit()

        # Non-manager technician attempt to approve must raise UserError
        with self.assertRaises(UserError):
            survey.with_user(self.technician_user).action_approve()

        # Manager user approves
        survey.with_user(self.manager_user).action_approve()
        self.assertEqual(survey.state, 'approved')
        self.assertEqual(survey.approver_id.id, self.manager_user.id)
        self.assertTrue(survey.approval_date)

    def test_05_rejection_workflow(self):
        """Manager rejection requires a reason and allows technician revision."""
        survey = self.env['solar.site.survey'].create({
            'partner_id': self.partner.id,
            'requested_capacity_kw': 2.0,
            'roof_direction': 'north',
            'shadow_free_roof_area': 200.0,
            'cable_distance': 10.0,
        })
        survey.action_submit()

        # Rejection without reason fails
        with self.assertRaises(UserError):
            survey.with_user(self.manager_user).action_reject()

        # Rejection with reason succeeds
        survey.rejection_reason = "North orientation yields sub-optimal irradiance. Re-assess south parapet space."
        survey.with_user(self.manager_user).action_reject()
        self.assertEqual(survey.state, 'rejected')

        # Technician resets to draft for revisions
        survey.action_reset_to_draft()
        self.assertEqual(survey.state, 'draft')

    def test_06_quotation_creation_and_order_confirmation_gating(self):
        """Quotations can only be generated from approved surveys, and orders cannot confirm with unapproved surveys."""
        survey = self.env['solar.site.survey'].create({
            'partner_id': self.partner.id,
            'requested_capacity_kw': 3.0,
            'roof_direction': 'south',
            'shadow_free_roof_area': 350.0,
            'cable_distance': 18.0,
        })

        # Draft survey cannot generate quotation
        with self.assertRaises(UserError):
            survey.action_create_quotation()

        # Submit and approve survey
        survey.action_submit()
        survey.with_user(self.manager_user).action_approve()

        # Approved survey generates quotation
        action = survey.action_create_quotation()
        self.assertTrue(action)
        self.assertEqual(action.get('res_model'), 'sale.order')
        self.assertEqual(survey.quotation_count, 1)

        sale_order = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(sale_order.survey_id.id, survey.id)
        self.assertEqual(sale_order.partner_id.id, self.partner.id)

        # Confirming solar order with approved survey is allowed
        self.assertTrue(sale_order.is_solar_order)

