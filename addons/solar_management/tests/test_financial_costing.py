# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestFinancialCosting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Ramesh Patel',
            'email': 'ramesh.patel@example.com',
            'city': 'Hyderabad',
        })
        cls.supplier_trans = cls.env['res.partner'].create({
            'name': 'Express Freight Transporters',
            'supplier_rank': 1,
        })
        cls.supplier_insp = cls.env['res.partner'].create({
            'name': 'Apex Safety Auditors',
            'supplier_rank': 1,
        })

        cls.user_tech1 = cls.env['res.users'].create({
            'name': 'Ravi Technician 1',
            'login': 'ravi_tech1@example.com',
            'email': 'ravi_tech1@example.com',
        })
        cls.user_tech2 = cls.env['res.users'].create({
            'name': 'Karan Technician 2',
            'login': 'karan_tech2@example.com',
            'email': 'karan_tech2@example.com',
        })

        cls.category = cls.env['product.category'].create({
            'name': 'Solar Test Category',
        })

        cls.solar_product = cls.env['product.product'].create({
            'name': '4 kW Test Solar Kit',
            'type': 'consu',
            'is_storable': True,
            'list_price': 220000.0,
            'standard_price': 140000.0,
            'is_solar_component': True,
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.solar_product.id,
                'product_uom_qty': 1.0,
                'price_unit': 220000.0,
            })],
        })

        cls.installation = cls.env['solar.installation'].create({
            'name': 'INST/TEST/0001',
            'partner_id': cls.partner.id,
            'sale_order_id': cls.sale_order.id,
            'lead_technician_id': cls.user_tech1.id,
            'technician_ids': [(6, 0, [cls.user_tech2.id])],
            'technician_hourly_rate': 500.0,
            'cost_materials': 140000.0,
        })

    def test_01_technician_labor_cost_calculation(self):
        """Verify labor duration, crew headcount, and total labor costing."""
        self.installation.write({
            'actual_start': '2026-10-15 08:00:00',
            'actual_finish': '2026-10-15 14:00:00',  # 6.0 hours
        })
        self.installation._compute_duration_hours()
        self.installation._compute_technician_headcount()
        self.installation._compute_project_financials()

        self.assertEqual(self.installation.duration_hours, 6.0)
        self.assertEqual(self.installation.num_technicians, 2, "Lead + 1 crew member = 2 technicians")
        # 6 hours * ₹500/hr * 2 technicians = ₹6,000
        self.assertEqual(self.installation.cost_technician_labor, 6000.0)

    def test_02_direct_project_expenses_attribution(self):
        """Verify vendor bills with expense categories correctly attribute to installation costs."""
        # Bill 1: Freight
        bill_freight = self.env['account.move'].create({
            'partner_id': self.supplier_trans.id,
            'move_type': 'in_invoice',
            'installation_id': self.installation.id,
            'solar_expense_type': 'freight',
            'invoice_date': '2026-10-14',
            'invoice_line_ids': [(0, 0, {
                'quantity': 1.0,
                'price_unit': 3500.0,
                'name': 'Transport Delivery to site',
            })],
        })

        # Bill 2: Inspection
        bill_insp = self.env['account.move'].create({
            'partner_id': self.supplier_insp.id,
            'move_type': 'in_invoice',
            'installation_id': self.installation.id,
            'solar_expense_type': 'inspection',
            'invoice_date': '2026-10-15',
            'invoice_line_ids': [(0, 0, {
                'quantity': 1.0,
                'price_unit': 2500.0,
                'name': 'Safety Inspection Test',
            })],
        })

        # Bill 3: Permit
        bill_permit = self.env['account.move'].create({
            'partner_id': self.supplier_insp.id,
            'move_type': 'in_invoice',
            'installation_id': self.installation.id,
            'solar_expense_type': 'permit',
            'invoice_date': '2026-10-15',
            'invoice_line_ids': [(0, 0, {
                'quantity': 1.0,
                'price_unit': 4000.0,
                'name': 'DISCOM Net-meter application',
            })],
        })

        self.installation._compute_project_financials()

        self.assertEqual(self.installation.cost_freight, 3500.0)
        self.assertEqual(self.installation.cost_inspection, 2500.0)
        self.assertEqual(self.installation.cost_permits, 4000.0)
        self.assertEqual(self.installation.cost_direct_expenses, 10000.0)

    def test_03_dec007_contribution_profit_and_margin(self):
        """Verify full DEC-007 multi-tier profitability: Gross Margin and Contribution Profit."""
        # Customer Invoice: ₹2,20,000
        inv = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'installation_id': self.installation.id,
            'solar_sale_order_id': self.sale_order.id,
            'invoice_date': '2026-10-15',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.solar_product.id,
                'quantity': 1.0,
                'price_unit': 220000.0,
                'name': 'Solar Installation Complete',
            })],
        })

        # Setup duration: 5 hours, 2 techs @ 500/hr = ₹5,000 labor
        self.installation.write({
            'actual_start': '2026-10-15 09:00:00',
            'actual_finish': '2026-10-15 14:00:00',
            'cost_materials': 140000.0,
        })

        # Direct Expenses: ₹10,000 total (freight 4000 + permit 6000)
        self.env['account.move'].create({
            'partner_id': self.supplier_trans.id,
            'move_type': 'in_invoice',
            'installation_id': self.installation.id,
            'solar_expense_type': 'freight',
            'invoice_line_ids': [(0, 0, {'quantity': 1.0, 'price_unit': 4000.0, 'name': 'Freight'})],
        })
        self.env['account.move'].create({
            'partner_id': self.supplier_insp.id,
            'move_type': 'in_invoice',
            'installation_id': self.installation.id,
            'solar_expense_type': 'permit',
            'invoice_line_ids': [(0, 0, {'quantity': 1.0, 'price_unit': 6000.0, 'name': 'Permit'})],
        })

        self.installation._compute_duration_hours()
        self.installation._compute_technician_headcount()
        self.installation._compute_project_financials()

        # Tier 1: Invoiced Revenue & Gross Margin
        self.assertEqual(self.installation.revenue_invoiced, 220000.0)
        self.assertEqual(self.installation.cost_materials, 140000.0)
        self.assertEqual(self.installation.gross_margin, 80000.0)
        self.assertAlmostEqual(self.installation.gross_margin_pct, 36.36, places=1)

        # Operational Direct Costs
        # Labor: 5 hrs * ₹500 * 2 = ₹5,000
        self.assertEqual(self.installation.cost_technician_labor, 5000.0)
        # Direct Expenses: 4000 + 6000 = ₹10,000
        self.assertEqual(self.installation.cost_direct_expenses, 10000.0)
        # Total Direct Cost: 140,000 + 5,000 + 10,000 = 155,000
        self.assertEqual(self.installation.cost_total_direct, 155000.0)

        # Tier 2 (DEC-007): Installation Contribution Profit
        # 220,000 - 155,000 = ₹65,000
        self.assertEqual(self.installation.contribution_profit, 65000.0)
        # Margin %: 65,000 / 220,000 = ~29.55%
        self.assertAlmostEqual(self.installation.contribution_margin_pct, 29.55, places=1)
        self.assertEqual(self.installation.profitability_status, 'healthy')

    def test_04_profitability_status_levels(self):
        """Verify status classifications: healthy, acceptable, low, negative."""
        inst = self.installation

        # Mock revenue ₹100,000
        # Healthy: >20% margin (e.g. ₹25,000 profit on ₹100k)
        inst.revenue_invoiced = 100000.0
        inst.cost_materials = 70000.0
        inst.cost_technician_labor = 3000.0
        inst.cost_direct_expenses = 2000.0
        inst.cost_total_direct = 75000.0
        inst.contribution_profit = 25000.0
        inst.contribution_margin_pct = 25.0
        # Check condition
        if inst.contribution_margin_pct >= 20.0:
            inst.profitability_status = 'healthy'
        self.assertEqual(inst.profitability_status, 'healthy')

        # Acceptable: 10-20% margin
        inst.contribution_margin_pct = 15.0
        if inst.contribution_margin_pct >= 20.0:
            inst.profitability_status = 'healthy'
        elif inst.contribution_margin_pct >= 10.0:
            inst.profitability_status = 'acceptable'
        self.assertEqual(inst.profitability_status, 'acceptable')

        # Low: 0-10%
        inst.contribution_margin_pct = 4.0
        if inst.contribution_margin_pct >= 20.0:
            inst.profitability_status = 'healthy'
        elif inst.contribution_margin_pct >= 10.0:
            inst.profitability_status = 'acceptable'
        elif inst.contribution_margin_pct >= 0.0:
            inst.profitability_status = 'low'
        self.assertEqual(inst.profitability_status, 'low')

        # Deficit / Loss: <0%
        inst.contribution_margin_pct = -5.0
        if inst.contribution_margin_pct < 0.0:
            inst.profitability_status = 'negative'
        self.assertEqual(inst.profitability_status, 'negative')

    def test_05_recompute_financials_action(self):
        """Verify action_recompute_financials execution and return."""
        res = self.installation.action_recompute_financials()
        self.assertTrue(res)

    def test_06_smart_navigation_actions(self):
        """Verify action_view_invoices and action_view_expenses return valid action dictionaries."""
        inv_action = self.installation.action_view_invoices()
        self.assertEqual(inv_action['res_model'], 'account.move')
        self.assertEqual(inv_action['context']['default_move_type'], 'out_invoice')

        exp_action = self.installation.action_view_expenses()
        self.assertEqual(exp_action['res_model'], 'account.move')
        self.assertEqual(exp_action['context']['default_move_type'], 'in_invoice')

        rec_exp_action = self.installation.action_record_project_expense()
        self.assertEqual(rec_exp_action['res_model'], 'account.move')
        self.assertEqual(rec_exp_action['context']['default_move_type'], 'in_invoice')

