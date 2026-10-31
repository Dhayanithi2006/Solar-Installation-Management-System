# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestSolarPackageBoM(TransactionCase):
    """Test suite for Subphase 2.2 Solar Package & BoM Management."""

    def test_01_solar_package_creation(self):
        """Verify that 3 kW On-Grid and Off-Grid packages exist with correct attributes."""
        pkg_on_grid_3kw = self.env.ref('solar_management.solar_package_on_grid_3kw')
        self.assertEqual(pkg_on_grid_3kw.capacity_kw, 3.0)
        self.assertEqual(pkg_on_grid_3kw.system_type, 'on_grid')
        self.assertEqual(pkg_on_grid_3kw.panel_count, 6)
        self.assertFalse(pkg_on_grid_3kw.battery_included)
        self.assertGreater(pkg_on_grid_3kw.standard_price, 0.0)

        pkg_off_grid_3kw = self.env.ref('solar_management.solar_package_off_grid_3kw')
        self.assertEqual(pkg_off_grid_3kw.capacity_kw, 3.0)
        self.assertEqual(pkg_off_grid_3kw.system_type, 'off_grid')
        self.assertTrue(pkg_off_grid_3kw.battery_included)

    def test_02_phantom_bom_configuration(self):
        """Verify that 3 kW On-Grid BoM is configured as a phantom kit and contains required parts."""
        bom = self.env.ref('solar_management.bom_on_grid_3kw')
        self.assertEqual(bom.type, 'phantom', "BoM must be configured as a 'phantom' kit")

        # Verify component types in BoM
        component_types = [
            line.product_id.product_tmpl_id.solar_component_type
            for line in bom.bom_line_ids
        ]
        self.assertIn('panel', component_types)
        self.assertIn('inverter', component_types)
        self.assertIn('charge_controller', component_types)
        self.assertIn('structure', component_types)
        self.assertIn('safety', component_types)
        self.assertIn('wiring', component_types)

        # 6 panels
        panel_line = bom.bom_line_ids.filtered(lambda l: l.product_id.solar_component_type == 'panel')
        self.assertEqual(panel_line.product_qty, 6.0)

    def test_03_off_grid_battery_enforcement(self):
        """Verify that an Off-Grid package without a battery raises a ValidationError."""
        kit_product = self.env['product.product'].create({
            'name': 'Test Invalid Off-Grid Kit',
            'type': 'consu',
            'is_storable': True,
        })
        invalid_bom = self.env['mrp.bom'].create({
            'product_tmpl_id': kit_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'phantom',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.env.ref('solar_management.product_solar_inverter_3kw').id,
                    'product_qty': 1.0,
                })
            ]
        })
        with self.assertRaises(ValidationError):
            self.env['solar.package'].create({
                'name': 'Invalid Off-Grid System',
                'system_type': 'off_grid',
                'capacity_kw': 3.0,
                'product_tmpl_id': kit_product.product_tmpl_id.id,
                'bom_id': invalid_bom.id,
            })

    def test_04_capacity_bounds_validation(self):
        """Verify that capacity must be between 1 kW and 5 kW."""
        kit_product = self.env.ref('solar_management.pkg_product_on_grid_1kw')
        bom = self.env.ref('solar_management.bom_on_grid_1kw')
        with self.assertRaises(ValidationError):
            self.env['solar.package'].create({
                'name': 'Out of Bounds 6kW System',
                'system_type': 'on_grid',
                'capacity_kw': 6.0,
                'product_tmpl_id': kit_product.product_tmpl_id.id,
                'bom_id': bom.id,
            })

