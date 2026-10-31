# -*- coding: utf-8 -*-
{
    'name': 'SunPower Solar Installation Management',
    'version': '18.0.1.0.0',
    'category': 'Operations/Solar',
    'sequence': 10,
    'summary': 'End-to-end solar quotation, site survey, installation, serialized warranty, and service management',
    'description': """
SunPower Solutions — Solar Installation Management System
==========================================================
Comprehensive Odoo ERP solution for residential and commercial rooftop solar installations:
- Customer solar enquiry capture (website & CRM)
- Rooftop site survey and mandatory approval gate
- Solar packages (1 kW to 5 kW On-Grid/Off-Grid) with automated BoMs
- Advance payment readiness verification
- Warehouse dispatch with mandatory serial scanning (inverter, battery, charge controller)
- Automatic warranty clock activation on delivery
- Mobile installation worksheets, power generation tests, and on-screen signature
- Service breakdown claims, warranty validation, and repair billing
- Executive dashboard: operational KPIs, material COGS, technician labor costs, and installation contribution profit
    """,
    'author': 'SunPower Solutions / Senior Odoo Technical Architect',
    'website': 'https://www.sunpower.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'website',
        'website_crm',
        'sale_management',
        'mrp',
        'stock',
        'purchase',
        'account',
        'project',
        'hr_timesheet',
        'repair',
        'barcode',
    ],
    'data': [
        'security/solar_security.xml',
        'security/ir.model.access.csv',
        'security/solar_rules.xml',
        'data/sequence_data.xml',
        'data/warranty_rule_data.xml',
        'data/solar_product_data.xml',
        'data/solar_package_data.xml',
        'data/solar_crm_data.xml',
        'data/solar_survey_data.xml',
        'data/solar_sale_data.xml',
        'data/solar_procurement_data.xml',
        'data/solar_reordering_data.xml',
        'data/solar_lot_data.xml',
        'data/solar_installation_data.xml',
        'data/solar_warranty_data.xml',
        'data/solar_service_data.xml',
        'data/solar_repair_data.xml',
        'data/solar_financial_data.xml',
        'data/solar_subsidy_data.xml',
        'data/solar_cron_data.xml',
        'views/product_views.xml',
        'views/package_views.xml',
        'views/crm_lead_views.xml',
        'views/site_survey_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_lot_views.xml',
        'views/installation_views.xml',
        'views/warranty_views.xml',
        'views/service_ticket_views.xml',
        'views/repair_order_views.xml',
        'views/account_move_views.xml',
        'views/subsidy_views.xml',
        'views/solar_passport_views.xml',
        'views/solar_menus.xml',
        'views/website_templates.xml',
        'report/solar_delivery_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
