# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSolarAddonFoundation(TransactionCase):
    """Foundational test suite for solar_management core addon."""

    def test_01_module_installed(self):
        """Verify that solar_management module is recognized and installable."""
        module = self.env['ir.module.module'].search([('name', '=', 'solar_management')])
        self.assertTrue(module, "Module 'solar_management' must exist in ir.module.module")

    def test_02_sequences_exist(self):
        """Verify that sequences for survey, installation, warranty, and tickets are created."""
        expected_codes = [
            'solar.site.survey',
            'solar.installation',
            'solar.warranty.record',
            'solar.subsidy.case',
            'solar.service.ticket',
        ]
        for code in expected_codes:
            seq = self.env['ir.sequence'].search([('code', '=', code)])
            self.assertTrue(seq, f"Sequence for '{code}' must exist")

    def test_03_all_ten_security_groups_exist(self):
        """Verify that all 10 defined role security groups exist in registry."""
        group_refs = [
            'solar_management.group_solar_user',
            'solar_management.group_solar_sales',
            'solar_management.group_solar_survey_tech',
            'solar_management.group_solar_survey_manager',
            'solar_management.group_solar_warehouse',
            'solar_management.group_solar_installer',
            'solar_management.group_solar_service',
            'solar_management.group_solar_service_manager',
            'solar_management.group_solar_accountant',
            'solar_management.group_solar_director',
            'solar_management.group_solar_manager',
        ]
        for ref in group_refs:
            group = self.env.ref(ref, raise_if_not_found=False)
            self.assertTrue(group, f"Security group '{ref}' must exist")

    def test_04_record_rules_exist(self):
        """Verify that key multi-company and role rules exist."""
        rule_refs = [
            'solar_management.solar_survey_company_rule',
            'solar_management.solar_installation_company_rule',
            'solar_management.solar_survey_technician_rule',
            'solar_management.solar_survey_manager_rule',
            'solar_management.solar_installation_crew_rule',
            'solar_management.solar_installation_admin_rule',
        ]
        for ref in rule_refs:
            rule = self.env.ref(ref, raise_if_not_found=False)
            self.assertTrue(rule, f"Record rule '{ref}' must exist")
