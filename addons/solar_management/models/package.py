# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SolarPackage(models.Model):
    _name = 'solar.package'
    _description = 'Solar Package & System Specification'
    _order = 'capacity_kw asc, system_type asc'

    name = fields.Char(
        string='Package Name',
        required=True,
        tracking=True
    )
    system_type = fields.Selection([
        ('on_grid', 'On-Grid (Grid-Tied)'),
        ('off_grid', 'Off-Grid (Battery Storage)'),
    ], string='System Type', required=True, default='on_grid')

    capacity_kw = fields.Float(
        string='System Capacity (kW)',
        required=True,
        default=3.0,
        help='System capacity in kilowatts (1 kW to 5 kW).'
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Package Kit Product',
        required=True,
        help='Sales kit product added to customer quotations.'
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        string='Bill of Materials (Kit BoM)',
        required=True,
        help='Kit Bill of Materials defining component explosion.'
    )
    list_price = fields.Float(
        string='Package Sale Price',
        related='product_tmpl_id.list_price',
        readonly=False
    )
    standard_price = fields.Float(
        string='Material Cost (BoM Sum)',
        compute='_compute_standard_price',
        store=True,
        readonly=True
    )
    battery_included = fields.Boolean(
        string='Battery Bank Included',
        compute='_compute_package_details',
        store=True
    )
    panel_count = fields.Integer(
        string='Solar Panel Count',
        compute='_compute_package_details',
        store=True
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends('bom_id', 'bom_id.bom_line_ids', 'bom_id.bom_line_ids.product_id.standard_price')
    def _compute_standard_price(self):
        for pkg in self:
            cost = 0.0
            if pkg.bom_id:
                for line in pkg.bom_id.bom_line_ids:
                    cost += line.product_qty * line.product_id.standard_price
            pkg.standard_price = cost

    @api.depends('bom_id', 'bom_id.bom_line_ids', 'system_type')
    def _compute_package_details(self):
        for pkg in self:
            panel_qty = 0
            has_battery = False
            if pkg.bom_id:
                for line in pkg.bom_id.bom_line_ids:
                    comp_type = line.product_id.product_tmpl_id.solar_component_type
                    if comp_type == 'panel':
                        panel_qty += int(line.product_qty)
                    elif comp_type == 'battery':
                        has_battery = True
            pkg.panel_count = panel_qty
            pkg.battery_included = has_battery or (pkg.system_type == 'off_grid')

    @api.constrains('system_type', 'capacity_kw')
    def _check_capacity_range(self):
        for pkg in self:
            if pkg.capacity_kw < 1.0 or pkg.capacity_kw > 5.0:
                raise ValidationError(_("Package capacity must be between 1 kW and 5 kW."))

    @api.constrains('system_type', 'bom_id')
    def _check_off_grid_battery(self):
        for pkg in self:
            if pkg.system_type == 'off_grid' and pkg.bom_id:
                has_battery = any(
                    line.product_id.product_tmpl_id.solar_component_type == 'battery'
                    for line in pkg.bom_id.bom_line_ids
                )
                if not has_battery:
                    raise ValidationError(_("Off-Grid packages must include a battery in their Bill of Materials."))

