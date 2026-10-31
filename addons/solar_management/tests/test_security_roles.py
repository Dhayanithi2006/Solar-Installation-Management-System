# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestSecurityRoles(TransactionCase):
    """
    Subphase 5.2 Security Audit Suite:
    Validates all 10 security roles, group inheritance, model ACL permissions,
    multi-company isolation rules, and technician domain filtering rules.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.expected_groups = [
            'group_solar_user',
            'group_solar_sales',
            'group_solar_survey_tech',
            'group_solar_survey_manager',
            'group_solar_warehouse',
            'group_solar_installer',
            'group_solar_service',
            'group_solar_service_manager',
            'group_solar_accountant',
            'group_solar_director',
            'group_solar_manager',
        ]

        cls.models_to_check = [
            'solar.site.survey',
            'solar.package',
            'solar.installation',
            'solar.warranty.record',
            'solar.warranty.rule',
            'solar.service.ticket',
            'solar.subsidy.case',
            'solar.subsidy.document',
        ]

    def test_01_all_10_security_groups_exist(self):
        """Verify that every security role is registered under Solar Installation Management category."""
        category = self.env.ref('solar_management.module_category_solar_management', raise_if_not_found=False)
        self.assertTrue(category, "Module category 'Solar Installation Management' must exist")

        for xml_id in self.expected_groups:
            group = self.env.ref(f'solar_management.{xml_id}', raise_if_not_found=False)
            self.assertTrue(group, f"Security group '{xml_id}' must be registered")
            self.assertEqual(group.category_id, category, f"Group '{xml_id}' must belong to Solar Management category")

    def test_02_group_implications_hierarchy(self):
        """Verify role inheritance: operational groups imply group_solar_user, manager implies all."""
        base_user = self.env.ref('solar_management.group_solar_user')
        manager = self.env.ref('solar_management.group_solar_manager')

        # Every role implies base user directly or transitively
        for xml_id in self.expected_groups:
            if xml_id != 'group_solar_user':
                group = self.env.ref(f'solar_management.{xml_id}')
                all_implied = group.trans_implied_ids | group.implied_ids
                self.assertIn(
                    base_user,
                    all_implied,
                    f"Group '{xml_id}' must imply base group_solar_user directly or transitively"
                )

        # Manager group implies all operational groups
        for xml_id in self.expected_groups:
            target_group = self.env.ref(f'solar_management.{xml_id}')
            all_manager_implied = manager.trans_implied_ids | manager.implied_ids | manager
            self.assertIn(
                target_group,
                all_manager_implied,
                f"Manager group must imply '{xml_id}' for full operational governance"
            )

    def test_03_model_access_permissions(self):
        """Verify ACL permissions (ir.model.access) across all solar models."""
        for model_name in self.models_to_check:
            # Check read access for base user
            base_group = self.env.ref('solar_management.group_solar_user')
            access_user = self.env['ir.model.access'].search([
                ('model_id.model', '=', model_name),
                ('group_id', '=', base_group.id),
            ], limit=1)
            self.assertTrue(access_user, f"Model '{model_name}' must have ACL entry for group_solar_user")
            self.assertTrue(access_user.perm_read, f"Base user must have read permission on '{model_name}'")

            # Check full CRUD for manager
            manager_group = self.env.ref('solar_management.group_solar_manager')
            access_mgr = self.env['ir.model.access'].search([
                ('model_id.model', '=', model_name),
                ('group_id', '=', manager_group.id),
            ], limit=1)
            self.assertTrue(access_mgr, f"Model '{model_name}' must have ACL entry for group_solar_manager")
            self.assertTrue(access_mgr.perm_read, f"Manager must have read permission on '{model_name}'")
            self.assertTrue(access_mgr.perm_write, f"Manager must have write permission on '{model_name}'")
            self.assertTrue(access_mgr.perm_create, f"Manager must have create permission on '{model_name}'")
            self.assertTrue(access_mgr.perm_unlink, f"Manager must have unlink permission on '{model_name}'")

    def test_04_multi_company_record_rules(self):
        """Verify multi-company record rules exist and enforce company_ids domain."""
        company_models = [
            'solar.site.survey',
            'solar.installation',
            'solar.warranty.record',
            'solar.service.ticket',
            'solar.subsidy.case',
        ]
        for model_name in company_models:
            rule = self.env['ir.rule'].search([
                ('model_id.model', '=', model_name),
                ('name', 'ilike', 'multi-company'),
            ], limit=1)
            self.assertTrue(rule, f"Multi-company rule must exist for model '{model_name}'")
            self.assertIn('company_id', rule.domain_force)

    def test_05_technician_installation_rule(self):
        """Verify technician crew record rule filters installations to assigned jobs."""
        rule = self.env.ref('solar_management.solar_installation_crew_rule', raise_if_not_found=False)
        self.assertTrue(rule, "Installation crew record rule must exist")
        self.assertIn('technician_ids', rule.domain_force)
        self.assertIn('lead_technician_id', rule.domain_force)

    def test_06_survey_technician_rule(self):
        """Verify survey technician record rule filters surveys to assigned technician."""
        rule = self.env.ref('solar_management.solar_survey_technician_rule', raise_if_not_found=False)
        self.assertTrue(rule, "Survey technician record rule must exist")
        self.assertIn('technician_id', rule.domain_force)

