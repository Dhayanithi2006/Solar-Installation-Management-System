# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields
from datetime import timedelta


class TestSolarEndToEndLifecycle(TransactionCase):
    """
    End-to-End Integration Test Runner: SunPower Solutions Solar Installation Management System.
    Validates the complete single-threaded lifecycle of customer Arun Kumar across all 6 mandatory business scenarios:
      1. Rooftop enquiry, CRM qualification, technical site survey, and mandatory approval gate.
      2. 3 kW On-Grid package quotation, BoM kit calculation, 20% advance payment gate, and operations handoff.
      3. Serial scanning on dispatch (stock.lot), customer linking, and automatic warranty activation on delivery date.
      4. Mobile installation worksheet, capacity, timestamps, power generation test, photo evidence, and on-screen customer signature.
      5. 18-month breakdown, serial/warranty lookup, ₹0 covered repair vs parts/labor billing, customer confirmation closure gate.
      6. Director dashboard with operational KPIs, material COGS, technician labor costs, attributable project expenses, and installation contribution profit (DEC-007).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # -----------------------------------------------------------------
        # 1. User Roles & Security Infrastructure
        # -----------------------------------------------------------------
        cls.user_sales = cls.env['res.users'].create({
            'name': 'Sales Rep Arun Kumar',
            'login': 'e2e_sales_rep',
            'email': 'sales_e2e@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_sales').id])],
        })
        cls.user_survey_mgr = cls.env['res.users'].create({
            'name': 'Survey Approver Manager',
            'login': 'e2e_survey_mgr',
            'email': 'survey_mgr_e2e@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_survey_manager').id])],
        })
        cls.user_warehouse = cls.env['res.users'].create({
            'name': 'Warehouse Manager Dispatch',
            'login': 'e2e_warehouse',
            'email': 'warehouse_e2e@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_warehouse').id])],
        })
        cls.user_lead_tech = cls.env['res.users'].create({
            'name': 'Senior Lead Technician Rooftop',
            'login': 'e2e_lead_tech',
            'email': 'lead_tech_e2e@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_installer').id])],
        })

        # -----------------------------------------------------------------
        # 2. Customer Partner: Arun Kumar
        # -----------------------------------------------------------------
        cls.partner = cls.env['res.partner'].create({
            'name': 'Arun Kumar',
            'phone': '+91 98480 22334',
            'email': 'arun.kumar@example.com',
            'street': 'Flat 402, Green Meadows, Jubilee Hills',
            'city': 'Hyderabad',
        })

        # -----------------------------------------------------------------
        # 3. Hardware Catalog & Serial-Tracked Inverter
        # -----------------------------------------------------------------
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        cls.prod_inverter_3kw = cls.env['product.product'].create({
            'name': 'SunPower Inverter 3 kW Single Phase On-Grid',
            'is_storable': True,
            'tracking': 'serial',
            'is_solar_component': True,
            'solar_component_type': 'inverter',
            'list_price': 32000.0,
            'standard_price': 25000.0,
        })
        cls.prod_panel_540w = cls.env['product.product'].create({
            'name': 'SunPower Mono PERC Solar Panel 540W',
            'is_storable': True,
            'tracking': 'none',
            'is_solar_component': True,
            'solar_component_type': 'panel',
            'list_price': 14500.0,
            'standard_price': 10500.0,
        })
        cls.prod_mounting = cls.env['product.product'].create({
            'name': 'Anodized Aluminum Rooftop Mounting Structure 3kW',
            'is_storable': True,
            'tracking': 'none',
            'is_solar_component': True,
            'solar_component_type': 'structure',
            'list_price': 16000.0,
            'standard_price': 11000.0,
        })
        cls.prod_ac_dc_box = cls.env['product.product'].create({
            'name': 'AC/DC Distribution & Safety Protection Box',
            'is_storable': True,
            'tracking': 'none',
            'is_solar_component': True,
            'solar_component_type': 'box',
            'list_price': 8000.0,
            'standard_price': 5000.0,
        })

        # -----------------------------------------------------------------
        # 4. Solar Package & Kit BoM
        # -----------------------------------------------------------------
        cls.prod_package_3kw = cls.env['product.product'].create({
            'name': 'Complete 3 kW On-Grid Solar Rooftop Kit',
            'is_storable': True,
            'is_solar_component': True,
            'solar_component_type': 'panel',
            'list_price': 189000.0,
            'standard_price': 126000.0,
        })

        cls.bom_3kw = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.prod_package_3kw.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'phantom',
            'bom_line_ids': [
                (0, 0, {'product_id': cls.prod_inverter_3kw.id, 'product_qty': 1.0}),
                (0, 0, {'product_id': cls.prod_panel_540w.id, 'product_qty': 6.0}),
                (0, 0, {'product_id': cls.prod_mounting.id, 'product_qty': 1.0}),
                (0, 0, {'product_id': cls.prod_ac_dc_box.id, 'product_qty': 1.0}),
            ],
        })

        cls.solar_package = cls.env['solar.package'].create({
            'name': '3 kW On-Grid System',
            'system_type': 'on_grid',
            'capacity_kw': 3.0,
            'product_tmpl_id': cls.prod_package_3kw.product_tmpl_id.id,
            'bom_id': cls.bom_3kw.id,
        })

        # -----------------------------------------------------------------
        # 5. Warranty Policies (Scenario 3 & 5)
        # -----------------------------------------------------------------
        cls.warranty_rule_inverter = cls.env['solar.warranty.rule'].create({
            'name': 'Inverter Standard 2-Year Warranty Policy',
            'product_id': cls.prod_inverter_3kw.id,
            'warranty_period_months': 24,
            'state': 'active',
        })

        # -----------------------------------------------------------------
        # 6. Service Vendors for Project Attributable Expenses (DEC-007)
        # -----------------------------------------------------------------
        cls.vendor_transport = cls.env['res.partner'].create({
            'name': 'SpeedFast Heavy Transport Ltd',
            'supplier_rank': 1,
        })
        cls.vendor_inspector = cls.env['res.partner'].create({
            'name': 'Deccan Electrical Safety Inspection Agency',
            'supplier_rank': 1,
        })
        cls.vendor_discom = cls.env['res.partner'].create({
            'name': 'TSREDCO / TSSPDCL Net-Metering Liaison',
            'supplier_rank': 1,
        })

    def test_complete_solar_lifecycle_scenarios_1_to_6(self):
        """Execute and validate all 6 connected business scenarios sequentially."""

        # =====================================================================
        # SCENARIO 1: Enquiry, CRM Lead, Site Survey & Mandatory Approval Gate
        # =====================================================================
        # 1. Customer submits rooftop enquiry
        lead = self.env['crm.lead'].create({
            'name': 'Arun Kumar — 3 kW On-Grid Rooftop Solar Enquiry',
            'partner_id': self.partner.id,
            'contact_name': 'Arun Kumar',
            'phone': '+91 98480 22334',
            'requested_capacity_kw': 3.0,
            'requested_system_type': 'on_grid',
            'monthly_bill_amount': 4500.0,
            'roof_space_sqft': 380.0,
            'subsidy_interest': True,
        })
        self.assertTrue(lead.id, "CRM Lead must be created")

        # 2. Site Survey created from enquiry
        survey = self.env['solar.site.survey'].create({
            'lead_id': lead.id,
            'partner_id': self.partner.id,
            'requested_capacity_kw': 3.0,
            'system_type': 'on_grid',
            'roof_direction': 'south',
            'roof_tilt': 15.0,
            'shadow_free_roof_area': 350.0,
            'cable_distance': 18.0,
            'roof_structure': 'rcc',
            'shading_analysis': 'no_shade',
            'grid_suitability': 'suitable',
            'sanctioned_load_kw': 5.0,
            'state': 'draft',
        })
        self.assertEqual(survey.state, 'draft')

        # 3. Technician submits survey for approval
        survey.action_submit()
        self.assertEqual(survey.state, 'submitted')

        # 4. Mandatory Approval Gate: Check that quotation confirmation is blocked without approved survey
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'survey_id': survey.id,
            'package_id': self.solar_package.id,
            'order_line': [(0, 0, {
                'product_id': self.prod_package_3kw.id,
                'product_uom_qty': 1.0,
                'price_unit': 189000.0,
            })],
        })
        # Attempting confirmation while survey is still submitted MUST be blocked
        with self.assertRaises(ValidationError):
            order.action_confirm()

        # 5. Survey Manager reviews and approves survey
        survey.action_approve()
        self.assertEqual(survey.state, 'approved', "Site Survey must be in approved state")

        # =====================================================================
        # SCENARIO 2: Package BoM, Advance Payment Check & Downstream Operations
        # =====================================================================
        # 1. Verify advance payment requirement (20% = ₹37,800 on ₹1,89,000)
        order.advance_payment_policy = 'percentage'
        order.advance_percentage = 20.0
        order._compute_advance_amount_required()
        order._compute_advance_payment_status()
        self.assertEqual(order.advance_amount_required, 37800.0)
        self.assertEqual(order.advance_payment_status, 'pending')

        # 2. Advance Payment Gate: Confirming order without paying advance must be blocked
        with self.assertRaises(ValidationError):
            order.action_confirm()

        # 3. Customer pays advance payment
        order.action_record_advance_payment()
        order._compute_advance_payment_status()
        self.assertEqual(order.advance_payment_status, 'paid')
        self.assertTrue(order.work_ready, "Order must be work ready once advance is paid")

        # 4. Confirm sales order
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

        # 5. Verify auto-creation of Installation Job and Subsidy Case
        self.assertTrue(order.installation_ids, "Solar Installation Job must be auto-generated")
        installation = order.installation_ids[0]
        self.assertEqual(installation.partner_id, self.partner)

        self.assertTrue(order.subsidy_case_ids, "Government Subsidy Case must be auto-generated")
        subsidy_case = order.subsidy_case_ids[0]
        self.assertEqual(subsidy_case.partner_id, self.partner)

        # =====================================================================
        # SCENARIO 3: Warehouse Dispatch, Serial Validation & Warranty Activation
        # =====================================================================
        # 1. Create dispatch picking for the installation
        picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': picking_type_out.id,
            'location_id': picking_type_out.default_location_src_id.id,
            'location_dest_id': self.partner.property_stock_customer.id,
            'sale_id': order.id,
            'installation_id': installation.id,
            'origin': order.name,
        })

        # Add serial-tracked inverter move line
        move_inverter = self.env['stock.move'].create({
            'name': self.prod_inverter_3kw.name,
            'product_id': self.prod_inverter_3kw.id,
            'product_uom_qty': 1.0,
            'product_uom': self.uom_unit.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        picking.action_confirm()
        picking.action_assign()

        # 2. Validation Gate Check: Validating dispatch without serial scanning must be blocked
        with self.assertRaises(ValidationError):
            picking.button_validate()

        # 3. Assign unique serial number to the inverter
        lot_inverter = self.env['stock.lot'].create({
            'name': 'INV-AK-3KW-9901',
            'product_id': self.prod_inverter_3kw.id,
            'company_id': self.env.company.id,
        })
        picking.move_line_ids.write({
            'lot_id': lot_inverter.id,
            'quantity': 1.0,
        })

        # 4. Validate delivery dispatch
        picking.button_validate()
        self.assertEqual(picking.state, 'done', "Delivery picking must be completed")

        # 5. Verify equipment linked to Arun Kumar and installation
        self.assertEqual(lot_inverter.customer_id, self.partner)
        self.assertEqual(lot_inverter.installation_id, installation)

        # 6. Verify automated warranty activation on delivery date
        warranty = self.env['solar.warranty.record'].search([('lot_id', '=', lot_inverter.id)], limit=1)
        self.assertTrue(warranty, "Warranty record must be automatically activated on dispatch")
        self.assertEqual(warranty.state, 'active')
        self.assertEqual(warranty.warranty_period_months, 24, "Inverter warranty period must be 24 months")
        self.assertEqual(warranty.partner_id, self.partner)

        # =====================================================================
        # SCENARIO 4: Installation Worksheet, Generation Test & Acceptance Gate
        # =====================================================================
        # 1. Schedule installation crew
        installation.write({
            'lead_technician_id': self.user_lead_tech.id,
            'planned_start': fields.Datetime.now(),
            'planned_finish': fields.Datetime.now() + timedelta(hours=8),
        })
        installation.action_schedule()
        self.assertEqual(installation.state, 'scheduled')

        # 2. Technician commences work on rooftop
        installation.action_start_work()
        self.assertEqual(installation.state, 'in_progress')

        # 3. Log timestamps (7.5 hours duration)
        work_start = fields.Datetime.now() - timedelta(hours=7, minutes=30)
        work_finish = fields.Datetime.now()
        installation.write({
            'actual_start': work_start,
            'actual_finish': work_finish,
            'installed_capacity_kw': 3.0,
            'test_dc_voltage': 380.0,
            'test_ac_voltage': 232.0,
            'test_generation_kw': 2.85,
        })
        installation._compute_duration_hours()
        self.assertAlmostEqual(installation.duration_hours, 7.5, places=1)

        # 4. Mandatory Evidence Completion Gate: Action complete blocked without test + photos + signature
        with self.assertRaises(ValidationError):
            installation.action_complete()

        # 5. Satisfy all completion evidence requirements
        installation.write({
            'generation_confirmed': True,
            'installation_photo_array': b'fake_photo_array_content',
            'installation_photo_inverter': b'fake_photo_inverter_content',
            'customer_signature': b'fake_digital_signature_content',
            'customer_signed_by': 'Arun Kumar',
            'customer_signed_date': fields.Datetime.now(),
        })

        # 6. Complete and commission installation
        installation.action_complete()
        self.assertEqual(installation.state, 'completed', "Installation must be successfully commissioned")

        # =====================================================================
        # SCENARIO 5: 18-Month Breakdown, Warranty Lookup & Resolution Gate
        # =====================================================================
        # 1. Simulate breakdown 18 months post-delivery (within 24-month policy)
        simulated_claim_date = warranty.warranty_start + timedelta(days=545)  # ~18 months

        # Create support ticket
        ticket = self.env['solar.service.ticket'].create({
            'partner_id': self.partner.id,
            'lot_id': lot_inverter.id,
            'claim_date': simulated_claim_date,
            'fault_category': 'inverter_fault',
            'fault_description': 'Inverter display shows Error Code E04 (Grid Overvoltage Sync Failure).',
            'state': 'new',
        })
        ticket._compute_warranty_validation()
        self.assertEqual(ticket.warranty_record_id, warranty)
        self.assertEqual(ticket.warranty_coverage_status, 'covered', "18-month claim must be covered under 24m warranty")
        self.assertTrue(ticket.is_warranty_covered)

        # 2. Create Repair Order for ₹0 covered warranty work
        repair_action = ticket.action_create_repair_order()
        repair = self.env['repair.order'].search([('service_ticket_id', '=', ticket.id)], limit=1)
        self.assertTrue(repair, "Repair Order must be generated from service claim")
        self.assertTrue(repair.is_warranty_repair)
        self.assertEqual(repair.warranty_coverage, 'full_warranty')

        # Verify ₹0 covered billing rules
        repair.action_apply_warranty_billing_policy()
        self.assertEqual(repair.amount_total, 0.0, "Covered warranty repair order must be ₹0 total customer charge")

        # 3. Complete technical repair
        ticket.action_start_investigation()
        ticket.action_resolve_ticket()
        self.assertEqual(ticket.state, 'resolved')

        # 4. Mandatory Closure Gate: Attempting to close ticket before customer confirmation must be blocked
        with self.assertRaises(ValidationError):
            ticket.action_close_ticket()

        # 5. Customer confirms successful rooftop repair
        ticket.action_confirm_customer_resolution()
        self.assertTrue(ticket.customer_confirmed_resolution)

        # 6. Close ticket
        ticket.action_close_ticket()
        self.assertEqual(ticket.state, 'closed', "Service ticket must close after customer confirmation")

        # =====================================================================
        # SCENARIO 6: Invoicing, Costing, DEC-007 Contribution Profit & Subsidy
        # =====================================================================
        # 1. Customer Invoice (₹1,89,000)
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'installation_id': installation.id,
            'solar_sale_order_id': order.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.prod_package_3kw.id,
                'quantity': 1.0,
                'price_unit': 189000.0,
                'name': '3 kW Rooftop Solar System Installation',
            })],
        })

        # 2. Attributable Direct Project Expenses (Vendor Bills)
        # Bill 1: Freight
        self.env['account.move'].create({
            'partner_id': self.vendor_transport.id,
            'move_type': 'in_invoice',
            'installation_id': installation.id,
            'solar_expense_type': 'freight',
            'invoice_line_ids': [(0, 0, {'quantity': 1.0, 'price_unit': 3500.0, 'name': 'Panel Transport'})],
        })
        # Bill 2: CEIG Electrical Safety Inspection
        self.env['account.move'].create({
            'partner_id': self.vendor_inspector.id,
            'move_type': 'in_invoice',
            'installation_id': installation.id,
            'solar_expense_type': 'inspection',
            'invoice_line_ids': [(0, 0, {'quantity': 1.0, 'price_unit': 2500.0, 'name': 'CEIG Inspection'})],
        })
        # Bill 3: DISCOM Net-Metering Permit
        self.env['account.move'].create({
            'partner_id': self.vendor_discom.id,
            'move_type': 'in_invoice',
            'installation_id': installation.id,
            'solar_expense_type': 'permit',
            'invoice_line_ids': [(0, 0, {'quantity': 1.0, 'price_unit': 4000.0, 'name': 'Net-meter Permit'})],
        })

        # 3. Calculate DEC-007 Multi-Tier Profitability
        installation.cost_materials = 126000.0
        installation.technician_hourly_rate = 500.0
        installation.action_recompute_financials()

        # Invoiced Revenue
        self.assertEqual(installation.revenue_invoiced, 189000.0)

        # Material COGS & Tier 1 Gross Margin
        self.assertEqual(installation.cost_materials, 126000.0)
        self.assertEqual(installation.gross_margin, 63000.0)
        self.assertAlmostEqual(installation.gross_margin_pct, 33.33, places=1)

        # Operational Labor Cost (7.5h * ₹500 * 1 = ₹3,750)
        self.assertEqual(installation.cost_technician_labor, 3750.0)

        # Direct Expenses (3500 + 2500 + 4000 = ₹10,000)
        self.assertEqual(installation.cost_direct_expenses, 10000.0)

        # Total Direct Installation Cost (126k + 3.75k + 10k = ₹1,39,750)
        self.assertEqual(installation.cost_total_direct, 139750.0)

        # Tier 2 DEC-007 Contribution Profit (189k - 139.75k = ₹49,250)
        self.assertEqual(installation.contribution_profit, 49250.0)
        self.assertAlmostEqual(installation.contribution_margin_pct, 26.06, places=1)
        self.assertEqual(installation.profitability_status, 'healthy')

        # 4. Subsidy Case Pipeline & DBT Verification
        subsidy_case.write({
            'discom_name': 'tsspdcl',
            'consumer_number': '1002348892',
            'application_number': 'PMSGY/2026/TS/889211',
            'solar_capacity_kw': 3.0,
        })
        subsidy_case._compute_eligible_subsidy()
        self.assertEqual(subsidy_case.eligible_subsidy_amount, 78000.0, "3 kW receives ₹78,000 CFA")

        # Verify checklist and submit
        for doc in subsidy_case.document_ids.filtered(lambda d: d.is_mandatory):
            doc.action_verify()
        subsidy_case.action_submit()
        self.assertEqual(subsidy_case.state, 'submitted')

        # Sanction & Direct Benefit Transfer
        subsidy_case.action_approve_sanction()
        subsidy_case.action_record_disbursement()
        self.assertEqual(subsidy_case.state, 'disbursed')
        self.assertEqual(subsidy_case.disbursed_amount, 78000.0)

        # =====================================================================
        # LIFECYCLE SUMMARY: 100% End-to-End Success!
        # =====================================================================
        self.assertTrue(True, "All 6 business scenarios executed and validated seamlessly!")

