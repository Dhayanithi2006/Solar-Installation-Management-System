# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestSolarCrmEnquiry(TransactionCase):
    """Test CRM lead solar extensions, enquiry intake, and site survey hand-off."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sales_team = cls.env['crm.team'].create({
            'name': 'Test Solar Sales Team',
            'use_opportunities': True,
        })
        cls.lead = cls.env['crm.lead'].create({
            'name': 'Priya Sharma — 4 kW On-Grid',
            'contact_name': 'Priya Sharma',
            'phone': '+91 99887 76655',
            'email_from': 'priya.sharma@example.com',
            'street': '12 Gandhi Road',
            'city': 'Coimbatore',
            'requested_capacity_kw': 4.0,
            'requested_system_type': 'on_grid',
            'monthly_electricity_bill': 6200.0,
            'shadow_free_roof_area': 420.0,
            'grid_suitability': 'suitable',
            'subsidy_interest': True,
            'roof_space_notes': 'South-facing concrete terrace with clear horizon.',
            'team_id': cls.sales_team.id,
            'type': 'opportunity',
        })

    def test_01_lead_solar_fields_initial_state(self):
        """Verify solar-specific fields on CRM lead and default survey status."""
        self.assertEqual(self.lead.requested_capacity_kw, 4.0)
        self.assertEqual(self.lead.requested_system_type, 'on_grid')
        self.assertEqual(self.lead.monthly_electricity_bill, 6200.0)
        self.assertEqual(self.lead.shadow_free_roof_area, 420.0)
        self.assertTrue(self.lead.subsidy_interest)
        self.assertEqual(self.lead.survey_count, 0)
        self.assertEqual(self.lead.survey_status, 'no_survey')

    def test_02_action_create_site_survey(self):
        """Verify triggering survey creation auto-generates partner and passes specifications."""
        action = self.lead.action_create_site_survey()
        self.assertTrue(action)
        self.assertEqual(action.get('res_model'), 'solar.site.survey')

        # Check partner was auto-created and linked
        self.assertTrue(self.lead.partner_id)
        self.assertEqual(self.lead.partner_id.name, 'Priya Sharma')
        self.assertEqual(self.lead.partner_id.phone, '+91 99887 76655')

        # Check survey record values
        survey = self.env['solar.site.survey'].browse(action['res_id'])
        self.assertEqual(survey.lead_id.id, self.lead.id)
        self.assertEqual(survey.partner_id.id, self.lead.partner_id.id)
        self.assertEqual(survey.requested_capacity_kw, 4.0)
        self.assertEqual(survey.system_type, 'on_grid')
        self.assertEqual(survey.monthly_bill_amount, 6200.0)
        self.assertEqual(survey.shadow_free_roof_area, 420.0)
        self.assertEqual(survey.grid_suitability, 'suitable')
        self.assertEqual(survey.state, 'draft')

        # Verify compute fields on lead
        self.assertEqual(self.lead.survey_count, 1)
        self.assertEqual(self.lead.survey_status, 'draft')

    def test_03_survey_workflow_updates_lead_status(self):
        """Verify survey state progression reflects dynamically on the parent lead."""
        action = self.lead.action_create_site_survey()
        survey = self.env['solar.site.survey'].browse(action['res_id'])

        # Set technician measurements
        survey.write({
            'roof_direction': 'south',
            'roof_tilt': 18.0,
            'cable_distance': 15.0,
        })

        # Submit survey
        survey.action_submit()
        self.assertEqual(survey.state, 'submitted')
        self.assertEqual(self.lead.survey_status, 'submitted')

        # Approve survey
        survey.action_approve()
        self.assertEqual(survey.state, 'approved')
        self.assertEqual(self.lead.survey_status, 'approved')
        self.assertTrue(survey.approval_date)
        self.assertEqual(survey.approver_id.id, self.env.user.id)

