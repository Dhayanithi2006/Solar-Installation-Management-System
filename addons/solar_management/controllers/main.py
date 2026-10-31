# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request


class SolarEnquiryController(http.Controller):

    @http.route('/solar/enquiry', type='http', auth='public', website=True, sitemap=True)
    def solar_enquiry_form(self, **kw):
        """Render public rooftop solar inquiry form."""
        return request.render('solar_management.solar_enquiry_form_template', {})

    @http.route('/solar/enquiry/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def solar_enquiry_submit(self, **post):
        """Handle solar enquiry form submission and generate qualified CRM lead."""
        name = post.get('name') or _('Rooftop Solar Enquiry')
        phone = post.get('phone')
        email = post.get('email')
        street = post.get('street')
        city = post.get('city')
        requested_capacity = float(post.get('requested_capacity_kw') or 3.0)
        system_type = post.get('system_type') or 'on_grid'
        monthly_bill = float(post.get('monthly_electricity_bill') or 0.0)
        roof_area = float(post.get('shadow_free_roof_area') or 0.0)
        subsidy_interest = post.get('subsidy_interest') in ('true', 'True', '1', 'on')
        notes = post.get('roof_space_notes')

        # Find or create partner
        partner = False
        if email or phone:
            domain = []
            if email:
                domain.append(('email', '=ilike', email))
            if phone:
                domain.append(('phone', '=', phone))
            partner = request.env['res.partner'].sudo().search(domain, limit=1)

        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': name,
                'phone': phone,
                'email': email,
                'street': street,
                'city': city,
                'customer_rank': 1,
            })

        # Find Solar Sales Team
        team = request.env['crm.team'].sudo().search([('name', 'ilike', 'solar')], limit=1)

        # Create CRM Lead
        lead_vals = {
            'name': f"{name} — {requested_capacity} kW {dict(on_grid='On-Grid', off_grid='Off-Grid').get(system_type, '')} Solar",
            'partner_id': partner.id,
            'contact_name': name,
            'phone': phone,
            'email_from': email,
            'street': street,
            'city': city,
            'requested_capacity_kw': requested_capacity,
            'requested_system_type': system_type,
            'monthly_electricity_bill': monthly_bill,
            'shadow_free_roof_area': roof_area,
            'subsidy_interest': subsidy_interest,
            'roof_space_notes': notes,
            'team_id': team.id if team else False,
            'type': 'opportunity',
        }
        lead = request.env['crm.lead'].sudo().create(lead_vals)

        return request.redirect(f'/solar/enquiry/thank-you?lead_id={lead.id}')

    @http.route('/solar/enquiry/thank-you', type='http', auth='public', website=True)
    def solar_enquiry_thank_you(self, lead_id=None, **kw):
        """Render confirmation and thank you page."""
        lead = False
        if lead_id:
            lead = request.env['crm.lead'].sudo().browse(int(lead_id))
        return request.render('solar_management.solar_enquiry_thank_you_template', {'lead': lead})

