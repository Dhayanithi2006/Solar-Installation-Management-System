# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields


class TestSubsidyAnalytics(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Pooja Reddy',
            'email': 'pooja.reddy@example.com',
            'city': 'Hyderabad',
        })

        cls.doc_type_id = cls.env['solar.subsidy.document.type'].create({
            'name': 'National ID / Aadhaar',
            'code': 'ID_TEST',
            'sequence': 10,
            'is_mandatory': True,
        })
        cls.doc_type_bill = cls.env['solar.subsidy.document.type'].create({
            'name': 'Discom Power Bill',
            'code': 'BILL_TEST',
            'sequence': 20,
            'is_mandatory': True,
        })
        cls.doc_type_optional = cls.env['solar.subsidy.document.type'].create({
            'name': 'Optional Extra Photo',
            'code': 'PHOTO_TEST',
            'sequence': 30,
            'is_mandatory': False,
        })

        cls.subsidy_case = cls.env['solar.subsidy.case'].create({
            'partner_id': cls.partner.id,
            'scheme_name': 'PM Surya Ghar: Muft Bijli Yojana',
            'discom_name': 'tsspdcl',
            'consumer_number': '1008899221',
            'application_number': 'PMSGY/2026/TS/998822',
        })

    def test_01_subsidy_capacity_tier_calculation(self):
        """Verify PM Surya Ghar Central Financial Assistance tiers (1kW=30k, 2kW=60k, >=3kW=78k)."""
        case = self.subsidy_case

        case.solar_capacity_kw = 1.0
        case._compute_eligible_subsidy()
        self.assertEqual(case.eligible_subsidy_amount, 30000.0, "1 kW system eligible for ₹30,000 CFA")

        case.solar_capacity_kw = 2.0
        case._compute_eligible_subsidy()
        self.assertEqual(case.eligible_subsidy_amount, 60000.0, "2 kW system eligible for ₹60,000 CFA")

        case.solar_capacity_kw = 3.0
        case._compute_eligible_subsidy()
        self.assertEqual(case.eligible_subsidy_amount, 78000.0, "3 kW system eligible for ₹78,000 CFA")

        case.solar_capacity_kw = 5.0
        case._compute_eligible_subsidy()
        self.assertEqual(case.eligible_subsidy_amount, 78000.0, "5 kW system capped at ₹78,000 standard CFA")

    def test_02_mandatory_document_checklist_generation(self):
        """Verify case creation pre-populates document checklist lines from active types."""
        case = self.subsidy_case
        self.assertGreater(case.document_count, 0, "Checklist lines should be generated")
        self.assertFalse(case.mandatory_docs_verified, "Mandatory documents not yet verified")

    def test_03_submission_blocked_without_mandatory_documents(self):
        """Verify action_submit is strictly gated if mandatory documents are not verified."""
        case = self.subsidy_case
        with self.assertRaises(ValidationError):
            case.action_submit()

    def test_04_successful_submission_gate_and_verification(self):
        """Verify action_submit succeeds once mandatory documents are verified."""
        case = self.subsidy_case

        # Verify all mandatory documents
        for doc in case.document_ids.filtered(lambda d: d.is_mandatory):
            doc.action_verify()

        case._compute_document_status()
        self.assertTrue(case.mandatory_docs_verified, "All mandatory docs should now be verified")

        # Now submit should succeed
        case.action_submit()
        self.assertEqual(case.state, 'submitted', "Case should transition to submitted")

    def test_05_sanction_and_dbt_disbursement_lifecycle(self):
        """Verify workflow progression through Joint Inspection, Sanction, and DBT payout."""
        case = self.subsidy_case

        # Verify mandatory docs and submit
        for doc in case.document_ids.filtered(lambda d: d.is_mandatory):
            doc.action_verify()
        case.action_submit()

        # Joint Inspection Review
        case.action_start_review()
        self.assertEqual(case.state, 'under_review')

        # Sanction by DISCOM
        case.solar_capacity_kw = 3.0
        case._compute_eligible_subsidy()
        case.action_approve_sanction()
        self.assertEqual(case.state, 'approved')
        self.assertEqual(case.sanctioned_amount, 78000.0)

        # DBT Direct Credit
        case.action_record_disbursement()
        self.assertEqual(case.state, 'disbursed')
        self.assertEqual(case.disbursed_amount, 78000.0)
        self.assertTrue(case.disbursement_date)
        self.assertTrue(case.disbursement_reference)

    def test_06_installation_subsidies_link(self):
        """Verify installation action_view_subsidies smart button action."""
        installation = self.env['solar.installation'].create({
            'name': 'INST/TEST/SUB',
            'partner_id': self.partner.id,
            'sale_order_id': self.env['sale.order'].create({'partner_id': self.partner.id}).id,
        })
        self.subsidy_case.installation_id = installation.id
        installation._compute_subsidy_case_count()
        self.assertEqual(installation.subsidy_case_count, 1)

        action = installation.action_view_subsidies()
        self.assertEqual(action['res_model'], 'solar.subsidy.case')

