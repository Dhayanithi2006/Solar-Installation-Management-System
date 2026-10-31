# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSolarProductCatalogue(TransactionCase):
    """Test suite for Subphase 2.1 Solar Product Catalogue."""

    def test_01_product_categories_created(self):
        """Verify that solar product category tree exists."""
        root_categ = self.env.ref('solar_management.categ_solar_root', raise_if_not_found=False)
        self.assertTrue(root_categ, "Root category 'Solar Hardware & Systems' must exist")

        inverter_categ = self.env.ref('solar_management.categ_solar_inverters', raise_if_not_found=False)
        self.assertEqual(inverter_categ.parent_id, root_categ, "Inverters category must be under root solar category")

    def test_02_serialized_equipment_tracking(self):
        """Verify that inverters, batteries, and charge controllers are serial-tracked."""
        # 1. 3 kW Inverter
        inverter_3kw = self.env.ref('solar_management.product_solar_inverter_3kw')
        self.assertEqual(inverter_3kw.tracking, 'serial', "3 kW Inverter must have tracking='serial'")
        self.assertTrue(inverter_3kw.is_serial_required, "3 kW Inverter must require serial scan before dispatch")
        self.assertEqual(inverter_3kw.solar_capacity_watts, 3000.0)

        # 2. 150Ah Battery
        battery = self.env.ref('solar_management.product_solar_battery_150ah')
        self.assertEqual(battery.tracking, 'serial', "Battery must have tracking='serial'")
        self.assertTrue(battery.is_serial_required, "Battery must require serial scan before dispatch")

        # 3. MPPT Charge Controller
        controller = self.env.ref('solar_management.product_solar_charge_controller_mppt')
        self.assertEqual(controller.tracking, 'serial', "Charge controller must have tracking='serial'")
        self.assertTrue(controller.is_serial_required, "Charge controller must require serial scan")

    def test_03_panel_warranty_and_lot_tracking(self):
        """Verify solar panels have 20-year warranty policy and lot tracking."""
        panel = self.env.ref('solar_management.product_solar_panel_540w')
        self.assertEqual(panel.tracking, 'lot', "Panels should have lot tracking")
        self.assertEqual(panel.solar_capacity_watts, 540.0)
        self.assertTrue(panel.default_warranty_rule_id, "Panel must be linked to 20-year warranty rule")
        self.assertEqual(panel.default_warranty_rule_id.duration_value, 20)
        self.assertEqual(panel.default_warranty_rule_id.duration_unit, 'years')

    def test_04_suppliers_and_vendor_prices(self):
        """Verify that products are linked to suppliers for procurement."""
        inverter_3kw = self.env.ref('solar_management.product_solar_inverter_3kw')
        supplier_info = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', inverter_3kw.id)])
        self.assertTrue(supplier_info, "Inverter must have supplier info linked")
        self.assertEqual(supplier_info.partner_id.name, "Apex Inverter Technologies Pvt Ltd")

    def test_05_installation_service_type(self):
        """Verify that installation service is marked as a service type."""
        service = self.env.ref('solar_management.product_solar_installation_service')
        self.assertEqual(service.type, 'service', "Installation must have type='service'")
        self.assertEqual(service.solar_component_type, 'service')

