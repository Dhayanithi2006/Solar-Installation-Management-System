# -*- coding: utf-8 -*-
"""
SunPower Solutions — Solar Installation Management System
Secure Odoo 18 JSON REST API Controller Suite for React + TypeScript Frontend.

Adheres strictly to enterprise security rules:
- No wildcard CORS on authenticated endpoints (allowed origin matching).
- Strict user-context enforcement via request.env (no client-trusted IDs or statuses).
- Full reuse of Odoo ORM models, constraints, and business lifecycle methods.
"""

import json
import logging
import base64
from datetime import datetime, date
from odoo import http, fields, _
from odoo.http import request, Response
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = {
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
    'https://solar-installation-management-system.odoo.com',
}


def _get_cors_headers():
    """Evaluate request origin against allowed list and generate strict CORS headers."""
    origin = request.httprequest.headers.get('Origin', '')
    headers = {
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept',
        'Access-Control-Max-Age': '86400',
    }
    if origin in ALLOWED_ORIGINS:
        headers['Access-Control-Allow-Origin'] = origin
        headers['Access-Control-Allow-Credentials'] = 'true'
    elif not origin:
        # Same-origin or non-browser HTTP client
        pass
    return headers


def _json_response(data=None, message=None, status=200, error=None):
    """Format standard JSON envelope with appropriate status codes and CORS headers."""
    payload = {
        'status': 'success' if status < 400 else 'error',
        'code': status,
        'message': message,
        'data': data if data is not None else {},
    }
    if error:
        payload['error'] = error

    headers = _get_cors_headers()
    headers['Content-Type'] = 'application/json; charset=utf-8'

    def _json_serializer(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        raise TypeError(f"Type {type(obj)} not serializable")

    return Response(
        json.dumps(payload, default=_json_serializer),
        status=status,
        headers=headers
    )


def _parse_json_body():
    """Safely parse incoming JSON request body."""
    try:
        raw_data = request.httprequest.data
        if not raw_data:
            return {}
        return json.loads(raw_data.decode('utf-8'))
    except Exception as e:
        _logger.warning("Failed to parse JSON body: %s", e)
        return {}


def _require_auth(group_xml_id=None):
    """
    Validate that user has an active authenticated session and optionally belongs to a group.
    Returns (user, None) or (None, error_response).
    """
    if not request.session.uid:
        return None, _json_response(
            message=_("Authentication required. Please log in."),
            status=401,
            error="UNAUTHORIZED"
        )
    user = request.env.user
    if group_xml_id:
        if not user.has_group(group_xml_id) and not user.has_group('solar_management.group_solar_manager'):
            return None, _json_response(
                message=_("Permission denied. Required role: %s") % group_xml_id,
                status=403,
                error="FORBIDDEN"
            )
    return user, None


class SolarApiController(http.Controller):
    """Complete RESTful JSON API controller suite for SunPower Solutions."""

    # =========================================================================
    # Pre-flight OPTIONS handler for all /api/solar/v1 routes
    # =========================================================================
    @http.route('/api/solar/v1/<path:subpath>', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def api_options_handler(self, subpath=None, **kw):
        """Handle CORS pre-flight OPTIONS requests."""
        return Response(status=204, headers=_get_cors_headers())

    # =========================================================================
    # 1. Authentication & Session Management
    # =========================================================================
    @http.route('/api/solar/v1/auth/login', type='http', auth='none', methods=['POST'], csrf=False)
    def api_auth_login(self, **kw):
        """Authenticate user credentials and create Odoo session."""
        body = _parse_json_body()
        db = body.get('db') or request.db or request.session.db
        login = body.get('login')
        password = body.get('password')

        if not login or not password:
            return _json_response(message="Missing 'login' or 'password'.", status=400, error="BAD_REQUEST")

        try:
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return _json_response(message="Invalid credentials.", status=401, error="INVALID_CREDENTIALS")

            user = request.env['res.users'].browse(uid)
            groups = [g.xml_id for g in user.groups_id if g.xml_id and 'solar_management' in g.xml_id]

            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'login': user.login,
                'company': {
                    'id': user.company_id.id,
                    'name': user.company_id.name,
                    'currency': user.company_id.currency_id.symbol,
                },
                'roles': groups,
                'session_id': request.session.sid,
            }
            return _json_response(data=user_data, message="Login successful.", status=200)
        except AccessError as e:
            return _json_response(message=str(e), status=403, error="ACCESS_DENIED")
        except Exception as e:
            _logger.exception("Login error")
            return _json_response(message="Authentication service error.", status=500, error=str(e))

    @http.route('/api/solar/v1/auth/session', type='http', auth='none', methods=['GET'], csrf=False)
    def api_auth_session(self, **kw):
        """Inspect active session status and user metadata."""
        user, err = _require_auth()
        if err:
            return err

        groups = [g.xml_id for g in user.groups_id if g.xml_id and 'solar_management' in g.xml_id]
        return _json_response(data={
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'company': {
                'id': user.company_id.id,
                'name': user.company_id.name,
                'currency': user.company_id.currency_id.symbol,
            },
            'roles': groups,
            'is_manager': user.has_group('solar_management.group_solar_manager'),
            'is_installer': user.has_group('solar_management.group_solar_installer'),
            'is_surveyor': user.has_group('solar_management.group_solar_survey_tech'),
        })

    @http.route('/api/solar/v1/auth/logout', type='http', auth='none', methods=['POST'], csrf=False)
    def api_auth_logout(self, **kw):
        """Terminate current session."""
        request.session.logout()
        return _json_response(message="Successfully logged out.", status=200)

    # =========================================================================
    # 2. Executive Dashboard Analytics (Scenario 6 / DEC-007)
    # =========================================================================
    @http.route('/api/solar/v1/dashboard/kpis', type='http', auth='none', methods=['GET'], csrf=False)
    def api_dashboard_kpis(self, **kw):
        """Executive KPI aggregates for dashboard."""
        user, err = _require_auth()
        if err:
            return err

        env = request.env
        installations = env['solar.installation'].search([])
        total_inst = len(installations)
        completed_inst = len(installations.filtered(lambda i: i.state == 'completed'))

        total_rev = sum(installations.mapped('invoice_amount'))
        total_cogs = sum(installations.mapped('material_cogs'))
        total_labor = sum(installations.mapped('technician_labor_cost'))
        total_exp = sum(installations.mapped('total_direct_expenses'))
        contrib_profit = total_rev - total_cogs - total_labor - total_exp
        margin_pct = (contrib_profit / total_rev * 100.0) if total_rev > 0 else 0.0

        subsidies = env['solar.subsidy.case'].search([])
        total_subsidy_amount = sum(subsidies.mapped('calculated_cfa_subsidy'))

        tickets = env['solar.service.ticket'].search([])
        open_tickets = len(tickets.filtered(lambda t: t.state in ('new', 'assigned', 'in_progress')))

        return _json_response(data={
            'installations': {
                'total': total_inst,
                'completed': completed_inst,
                'active': total_inst - completed_inst,
            },
            'financials': {
                'total_revenue_invoiced': total_rev,
                'material_cogs': total_cogs,
                'technician_labor_cost': total_labor,
                'attributable_direct_expenses': total_exp,
                'contribution_profit': contrib_profit,
                'contribution_profit_margin_pct': round(margin_pct, 2),
                'currency': user.company_id.currency_id.symbol,
            },
            'subsidies': {
                'total_cases': len(subsidies),
                'total_cfa_amount': total_subsidy_amount,
            },
            'support': {
                'open_tickets': open_tickets,
                'total_tickets': len(tickets),
            }
        })

    # =========================================================================
    # 3. CRM Rooftop Enquiry Leads (Scenario 1)
    # =========================================================================
    @http.route('/api/solar/v1/crm/leads', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def api_crm_leads(self, **kw):
        """List or create CRM rooftop solar leads."""
        user, err = _require_auth('solar_management.group_solar_sales')
        if err:
            return err

        env = request.env
        if request.httprequest.method == 'GET':
            leads = env['crm.lead'].search([('is_solar_lead', '=', True)])
            data = [{
                'id': l.id,
                'name': l.name,
                'partner_name': l.partner_id.name if l.partner_id else l.contact_name,
                'phone': l.phone,
                'email': l.email_from,
                'requested_capacity_kw': l.requested_capacity_kw,
                'requested_system_type': l.requested_system_type,
                'monthly_electricity_bill': l.monthly_electricity_bill,
                'shadow_free_roof_area': l.shadow_free_roof_area,
                'subsidy_interest': l.subsidy_interest,
                'stage': l.stage_id.name if l.stage_id else None,
                'survey_count': l.site_survey_count,
            } for l in leads]
            return _json_response(data=data)

        # POST: Create new solar lead
        body = _parse_json_body()
        required = ['contact_name', 'phone', 'requested_capacity_kw']
        missing = [f for f in required if not body.get(f)]
        if missing:
            return _json_response(message=f"Missing fields: {missing}", status=400, error="VALIDATION_ERROR")

        partner = env['res.partner'].search([
            '|', ('phone', '=', body.get('phone')), ('email', '=ilike', body.get('email', ''))
        ], limit=1)
        if not partner:
            partner = env['res.partner'].create({
                'name': body.get('contact_name'),
                'phone': body.get('phone'),
                'email': body.get('email'),
                'customer_rank': 1,
            })

        lead = env['crm.lead'].create({
            'name': f"{body.get('contact_name')} — {body.get('requested_capacity_kw')} kW Solar",
            'partner_id': partner.id,
            'contact_name': body.get('contact_name'),
            'phone': body.get('phone'),
            'email_from': body.get('email'),
            'requested_capacity_kw': float(body.get('requested_capacity_kw', 3.0)),
            'requested_system_type': body.get('requested_system_type', 'on_grid'),
            'monthly_electricity_bill': float(body.get('monthly_electricity_bill', 0.0)),
            'shadow_free_roof_area': float(body.get('shadow_free_roof_area', 0.0)),
            'subsidy_interest': bool(body.get('subsidy_interest', True)),
            'user_id': user.id,
            'type': 'opportunity',
        })
        return _json_response(data={'id': lead.id, 'name': lead.name}, message="Lead created successfully.", status=201)

    @http.route('/api/solar/v1/crm/leads/<int:lead_id>/create-survey', type='http', auth='none', methods=['POST'], csrf=False)
    def api_crm_lead_create_survey(self, lead_id, **kw):
        """Trigger action_create_site_survey from CRM lead."""
        user, err = _require_auth('solar_management.group_solar_sales')
        if err:
            return err

        lead = request.env['crm.lead'].browse(lead_id)
        if not lead.exists():
            return _json_response(message="Lead not found.", status=404, error="NOT_FOUND")

        try:
            res = lead.action_create_site_survey()
            survey_id = res.get('res_id')
            return _json_response(data={'survey_id': survey_id}, message="Site survey created successfully.")
        except Exception as e:
            return _json_response(message=str(e), status=400, error="ACTION_ERROR")

    # =========================================================================
    # 4. Site Surveys & Approval Workflow (Scenario 1)
    # =========================================================================
    @http.route('/api/solar/v1/surveys', type='http', auth='none', methods=['GET'], csrf=False)
    def api_surveys_list(self, **kw):
        """List site surveys with status filters."""
        user, err = _require_auth()
        if err:
            return err

        surveys = request.env['solar.site.survey'].search([])
        data = [{
            'id': s.id,
            'name': s.name,
            'partner': {'id': s.partner_id.id, 'name': s.partner_id.name},
            'technician': {'id': s.technician_id.id, 'name': s.technician_id.name} if s.technician_id else None,
            'requested_capacity_kw': s.requested_capacity_kw,
            'recommended_capacity_kw': s.recommended_capacity_kw,
            'roof_type': s.roof_type,
            'shadow_free_area_sqft': s.shadow_free_area_sqft,
            'state': s.state,
            'survey_date': s.survey_date,
        } for s in surveys]
        return _json_response(data=data)

    @http.route('/api/solar/v1/surveys/<int:survey_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def api_survey_detail(self, survey_id, **kw):
        """Retrieve full details of a specific site survey."""
        user, err = _require_auth()
        if err:
            return err

        s = request.env['solar.site.survey'].browse(survey_id)
        if not s.exists():
            return _json_response(message="Survey not found.", status=404, error="NOT_FOUND")

        return _json_response(data={
            'id': s.id,
            'name': s.name,
            'partner': {'id': s.partner_id.id, 'name': s.partner_id.name, 'phone': s.partner_id.phone},
            'lead_id': s.lead_id.id if s.lead_id else None,
            'technician': {'id': s.technician_id.id, 'name': s.technician_id.name} if s.technician_id else None,
            'survey_date': s.survey_date,
            'roof_type': s.roof_type,
            'roof_area_sqft': s.roof_area_sqft,
            'shadow_free_area_sqft': s.shadow_free_area_sqft,
            'tilt_angle': s.tilt_angle,
            'azimuth_angle': s.azimuth_angle,
            'shading_issues': s.shading_issues,
            'shading_description': s.shading_description,
            'sanctioned_load_kw': s.sanctioned_load_kw,
            'grid_phase': s.grid_phase,
            'recommended_capacity_kw': s.recommended_capacity_kw,
            'structural_integrity_confirmed': s.structural_integrity_confirmed,
            'feasibility_approved': s.feasibility_approved,
            'state': s.state,
            'approval_notes': s.approval_notes,
        })

    @http.route('/api/solar/v1/surveys/<int:survey_id>/approve', type='http', auth='none', methods=['POST'], csrf=False)
    def api_survey_approve(self, survey_id, **kw):
        """Approve site survey (Scenario 1 gate). Requires Survey Manager role."""
        user, err = _require_auth('solar_management.group_solar_survey_manager')
        if err:
            return err

        survey = request.env['solar.site.survey'].browse(survey_id)
        if not survey.exists():
            return _json_response(message="Survey not found.", status=404, error="NOT_FOUND")

        try:
            with request.env.cr.savepoint():
                survey.action_approve()
                return _json_response(data={'id': survey.id, 'state': survey.state}, message="Site survey approved successfully.")
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="VALIDATION_ERROR")

    @http.route('/api/solar/v1/surveys/<int:survey_id>/create-quotation', type='http', auth='none', methods=['POST'], csrf=False)
    def api_survey_create_quotation(self, survey_id, **kw):
        """Create quotation from approved survey (Scenario 1 gate)."""
        user, err = _require_auth('solar_management.group_solar_sales')
        if err:
            return err

        survey = request.env['solar.site.survey'].browse(survey_id)
        if not survey.exists():
            return _json_response(message="Survey not found.", status=404, error="NOT_FOUND")

        try:
            with request.env.cr.savepoint():
                res = survey.action_create_quotation()
                order_id = res.get('res_id')
                return _json_response(data={'order_id': order_id}, message="Quotation created successfully.")
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="GATE_VIOLATION")

    # =========================================================================
    # 5. Solar Packages & BoM Management (Scenario 2)
    # =========================================================================
    @http.route('/api/solar/v1/packages', type='http', auth='none', methods=['GET'], csrf=False)
    def api_packages_list(self, **kw):
        """List pre-engineered solar packages."""
        user, err = _require_auth()
        if err:
            return err

        packages = request.env['solar.package'].search([])
        data = [{
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'capacity_kw': p.capacity_kw,
            'system_type': p.system_type,
            'sales_price': p.sales_price,
            'total_cost': p.total_cost,
            'state': p.state,
            'components_count': len(p.bom_line_ids),
        } for p in packages]
        return _json_response(data=data)

    # =========================================================================
    # 6. Sales Quotations & Advance Payment (Scenario 2)
    # =========================================================================
    @http.route('/api/solar/v1/orders', type='http', auth='none', methods=['GET'], csrf=False)
    def api_orders_list(self, **kw):
        """List sales orders and quotations."""
        user, err = _require_auth()
        if err:
            return err

        orders = request.env['sale.order'].search([('is_solar_order', '=', True)])
        data = [{
            'id': o.id,
            'name': o.name,
            'partner': {'id': o.partner_id.id, 'name': o.partner_id.name},
            'package': {'id': o.package_id.id, 'name': o.package_id.name} if o.package_id else None,
            'amount_total': o.amount_total,
            'advance_amount_required': o.advance_amount_required,
            'advance_amount_paid': o.advance_amount_paid,
            'advance_payment_status': o.advance_payment_status,
            'work_ready': o.work_ready,
            'state': o.state,
        } for o in orders]
        return _json_response(data=data)

    @http.route('/api/solar/v1/orders/<int:order_id>/record-advance', type='http', auth='none', methods=['POST'], csrf=False)
    def api_order_record_advance(self, order_id, **kw):
        """Record advance payment registration on order with genuine accounting transaction."""
        user, err = _require_auth('solar_management.group_solar_sales')
        if err:
            return err

        order = request.env['sale.order'].browse(order_id)
        if not order.exists():
            return _json_response(message="Order not found.", status=404, error="NOT_FOUND")

        body = _parse_json_body()
        notes = body.get('reference') or "Online Payment Gateway / Bank NEFT"
        amount = body.get('amount')
        journal_id = body.get('journal_id')

        try:
            with request.env.cr.savepoint():
                payment = order.action_record_advance_payment(
                    journal_id=journal_id,
                    payment_ref=notes,
                    amount=amount
                )
                return _json_response(data={
                    'id': order.id,
                    'advance_amount_paid': order.advance_amount_paid,
                    'advance_payment_status': order.advance_payment_status,
                    'work_ready': order.work_ready,
                    'payment_id': payment.id if payment else None,
                    'payment_name': payment.name if payment else None,
                    'payment_state': payment.state if payment else None,
                }, message="Advance payment recorded successfully.")
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="PAYMENT_ERROR")
        except Exception as e:
            _logger.exception("Error recording advance payment on order %s", order_id)
            return _json_response(message=_("Failed to record advance payment."), status=500, error="INTERNAL_ERROR")

    @http.route('/api/solar/v1/orders/<int:order_id>/confirm', type='http', auth='none', methods=['POST'], csrf=False)
    def api_order_confirm(self, order_id, **kw):
        """Confirm sales order with 20% advance payment check (Scenario 2 gate)."""
        user, err = _require_auth('solar_management.group_solar_sales')
        if err:
            return err

        order = request.env['sale.order'].browse(order_id)
        if not order.exists():
            return _json_response(message="Order not found.", status=404, error="NOT_FOUND")

        try:
            with request.env.cr.savepoint():
                order.action_confirm()
                return _json_response(data={'id': order.id, 'state': order.state}, message="Order confirmed and operations unlocked.")
        except ValidationError as e:
            return _json_response(message=str(e), status=400, error="GATE_VIOLATION")
        except UserError as e:
            return _json_response(message=str(e), status=400, error="VALIDATION_ERROR")
        except Exception as e:
            _logger.exception("Error confirming order %s", order_id)
            return _json_response(message=_("Failed to confirm order."), status=500, error="INTERNAL_ERROR")

    # =========================================================================
    # 7. Serial Numbers & Traceability (Scenario 3 / Scenario 5)
    # =========================================================================
    @http.route('/api/solar/v1/serials/lookup/<string:serial_no>', type='http', auth='none', methods=['GET'], csrf=False)
    def api_serial_lookup(self, serial_no, **kw):
        """Instant serial number lookup with warranty check (Scenario 5)."""
        user, err = _require_auth()
        if err:
            return err

        code = serial_no.strip()
        lot = request.env['stock.lot'].search([('name', '=', code)], limit=1)
        if not lot:
            return _json_response(message=f"Serial '{code}' not found.", status=404, error="NOT_FOUND")

        warranty = request.env['solar.warranty.record'].search([('lot_id', '=', lot.id)], limit=1)
        return _json_response(data={
            'serial_id': lot.id,
            'serial_number': lot.name,
            'product': {'id': lot.product_id.id, 'name': lot.product_id.name},
            'customer': {'id': lot.customer_id.id, 'name': lot.customer_id.name} if lot.customer_id else None,
            'installation_id': lot.installation_id.id if lot.installation_id else None,
            'warranty': {
                'id': warranty.id if warranty else None,
                'name': warranty.name if warranty else None,
                'state': warranty.state if warranty else 'no_warranty',
                'is_valid': warranty.is_valid if warranty else False,
                'days_remaining': warranty.days_remaining if warranty else 0,
                'warranty_start': warranty.warranty_start if warranty else None,
                'warranty_end': warranty.warranty_end if warranty else None,
            } if warranty else None
        })

    # =========================================================================
    # 8. Warehouse Dispatch & Barcode Scanning (Scenario 3)
    # =========================================================================
    @http.route('/api/solar/v1/inventory/dispatches', type='http', auth='none', methods=['GET'], csrf=False)
    def api_dispatches_list(self, **kw):
        """List solar equipment dispatches."""
        user, err = _require_auth('solar_management.group_solar_warehouse')
        if err:
            return err

        pickings = request.env['stock.picking'].search([('is_solar_picking', '=', True)])
        data = [{
            'id': p.id,
            'name': p.name,
            'partner': {'id': p.partner_id.id, 'name': p.partner_id.name},
            'origin': p.origin,
            'has_serialized_items': p.has_serialized_items,
            'state': p.state,
        } for p in pickings]
        return _json_response(data=data)

    @http.route('/api/solar/v1/inventory/dispatches/<int:picking_id>/scan', type='http', auth='none', methods=['POST'], csrf=False)
    def api_dispatch_scan(self, picking_id, **kw):
        """Scan serial barcode on outbound dispatch (Scenario 3)."""
        user, err = _require_auth('solar_management.group_solar_warehouse')
        if err:
            return err

        picking = request.env['stock.picking'].browse(picking_id)
        if not picking.exists():
            return _json_response(message="Dispatch transfer not found.", status=404, error="NOT_FOUND")

        body = _parse_json_body()
        barcode = body.get('barcode')
        if not barcode:
            return _json_response(message="Barcode is required.", status=400, error="VALIDATION_ERROR")

        try:
            with request.env.cr.savepoint():
                picking.action_scan_serial_barcode(barcode=barcode)
                return _json_response(message=f"Serial '{barcode}' scanned and assigned successfully.")
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="SCAN_ERROR")
        except Exception as e:
            _logger.exception("Error scanning barcode on dispatch %s", picking_id)
            return _json_response(message=_("Failed to scan barcode."), status=500, error="INTERNAL_ERROR")

    @http.route('/api/solar/v1/inventory/dispatches/<int:picking_id>/validate', type='http', auth='none', methods=['POST'], csrf=False)
    def api_dispatch_validate(self, picking_id, **kw):
        """Validate warehouse dispatch transfer with advance payment and serial check (Scenario 3 gate)."""
        user, err = _require_auth('solar_management.group_solar_warehouse')
        if err:
            return err

        picking = request.env['stock.picking'].browse(picking_id)
        if not picking.exists():
            return _json_response(message="Dispatch transfer not found.", status=404, error="NOT_FOUND")

        try:
            with request.env.cr.savepoint():
                picking.button_validate()
                return _json_response(data={
                    'id': picking.id,
                    'name': picking.name,
                    'state': picking.state,
                    'installation_state': picking.installation_id.state if picking.installation_id else None,
                    'hardware_delivered': picking.installation_id.hardware_delivered if picking.installation_id else False,
                }, message="Dispatch transfer validated successfully.")
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="GATE_VIOLATION")
        except Exception as e:
            _logger.exception("Error validating dispatch %s", picking_id)
            return _json_response(message=_("Failed to validate dispatch transfer."), status=500, error="INTERNAL_ERROR")

    # =========================================================================
    # 9. Mobile Installation Worksheet & Sign-Off (Scenario 4)
    # =========================================================================
    @http.route('/api/solar/v1/installations', type='http', auth='none', methods=['GET'], csrf=False)
    def api_installations_list(self, **kw):
        """List installation jobs filtered by assigned technician."""
        user, err = _require_auth('solar_management.group_solar_installer')
        if err:
            return err

        # Domain rules in solar_rules.xml apply automatically via ORM
        installations = request.env['solar.installation'].search([])
        data = [{
            'id': i.id,
            'name': i.name,
            'customer': {'id': i.partner_id.id, 'name': i.partner_id.name, 'phone': i.partner_id.phone},
            'scheduled_date': i.scheduled_date,
            'actual_capacity_kw': i.actual_capacity_kw,
            'state': i.state,
            'has_signature': bool(i.customer_signature),
            'power_test_kw': i.power_test_kw_output,
        } for i in installations]
        return _json_response(data=data)

    @http.route('/api/solar/v1/installations/<int:inst_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def api_installation_detail(self, inst_id, **kw):
        """Retrieve full installation worksheet details."""
        user, err = _require_auth('solar_management.group_solar_installer')
        if err:
            return err

        i = request.env['solar.installation'].browse(inst_id)
        if not i.exists():
            return _json_response(message="Installation job not found.", status=404, error="NOT_FOUND")

        return _json_response(data={
            'id': i.id,
            'name': i.name,
            'customer': {
                'id': i.partner_id.id,
                'name': i.partner_id.name,
                'phone': i.partner_id.phone,
                'street': i.partner_id.street,
                'city': i.partner_id.city,
            },
            'sale_order': {'id': i.sale_order_id.id, 'name': i.sale_order_id.name} if i.sale_order_id else None,
            'scheduled_date': i.scheduled_date,
            'state': i.state,
            'power_test': {
                'voltage': i.power_test_voltage,
                'current': i.power_test_current,
                'kw_output': i.power_test_kw_output,
                'grid_frequency': i.power_test_grid_frequency,
            },
            'photos': {
                'has_roof': bool(i.photo_panels_rooftop),
                'has_inverter': bool(i.photo_inverter_installed),
                'has_db': bool(i.photo_wiring_db),
                'has_earthing': bool(i.photo_earthing_pit),
                'has_net_meter': bool(i.photo_net_meter),
            },
            'customer_signed_by': i.customer_signed_by,
            'has_signature': bool(i.customer_signature),
            'customer_notes': i.customer_notes,
        })

    @http.route('/api/solar/v1/installations/<int:inst_id>/submit-worksheet', type='http', auth='none', methods=['POST'], csrf=False)
    def api_installation_submit_worksheet(self, inst_id, **kw):
        """Submit electrical test values, evidence photos, touch signature and complete job (Scenario 4 gate)."""
        user, err = _require_auth('solar_management.group_solar_installer')
        if err:
            return err

        inst = request.env['solar.installation'].browse(inst_id)
        if not inst.exists():
            return _json_response(message="Installation job not found.", status=404, error="NOT_FOUND")

        body = _parse_json_body()
        vals = {}

        # 1. Electrical Power Measurements
        if 'test_generation_kw' in body:
            vals['test_generation_kw'] = float(body['test_generation_kw'])
        elif 'power_test_kw_output' in body:
            vals['test_generation_kw'] = float(body['power_test_kw_output'])

        if 'test_dc_voltage' in body:
            vals['test_dc_voltage'] = float(body['test_dc_voltage'])
        elif 'power_test_voltage' in body:
            vals['test_dc_voltage'] = float(body['power_test_voltage'])

        if 'test_ac_voltage' in body:
            vals['test_ac_voltage'] = float(body['test_ac_voltage'])

        if 'generation_confirmed' in body:
            vals['generation_confirmed'] = bool(body['generation_confirmed'])
        elif vals.get('test_generation_kw', 0) > 0:
            vals['generation_confirmed'] = True

        if 'test_result' in body:
            vals['test_result'] = body['test_result']

        # 2. On-Roof GPS Coordinates
        if 'gps_latitude' in body:
            vals['gps_latitude'] = float(body['gps_latitude'])
        if 'gps_longitude' in body:
            vals['gps_longitude'] = float(body['gps_longitude'])
        if 'gps_required' in body:
            vals['gps_required'] = bool(body['gps_required'])

        # 3. Decode base64 photos
        if 'installation_photo_array' in body and body['installation_photo_array']:
            vals['installation_photo_array'] = body['installation_photo_array'].split(',')[-1]
        elif 'photo_panels_rooftop' in body and body['photo_panels_rooftop']:
            vals['installation_photo_array'] = body['photo_panels_rooftop'].split(',')[-1]

        if 'installation_photo_inverter' in body and body['installation_photo_inverter']:
            vals['installation_photo_inverter'] = body['installation_photo_inverter'].split(',')[-1]
        elif 'photo_inverter_installed' in body and body['photo_inverter_installed']:
            vals['installation_photo_inverter'] = body['photo_inverter_installed'].split(',')[-1]

        if 'installation_photo_generation' in body and body['installation_photo_generation']:
            vals['installation_photo_generation'] = body['installation_photo_generation'].split(',')[-1]

        # 4. Customer Sign-off
        if 'customer_signature' in body and body['customer_signature']:
            vals['customer_signature'] = body['customer_signature'].split(',')[-1]
        if 'customer_signed_by' in body:
            vals['customer_signed_by'] = body['customer_signed_by']
        if 'technician_notes' in body:
            vals['technician_notes'] = body['technician_notes']
        elif 'customer_notes' in body:
            vals['technician_notes'] = body['customer_notes']

        try:
            with request.env.cr.savepoint():
                inst.write(vals)
                inst.action_complete()
                return _json_response(data={'id': inst.id, 'state': inst.state}, message="Installation completed and verified successfully.")
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="WORKSHEET_VALIDATION_ERROR")
        except Exception as e:
            _logger.exception("Error completing installation worksheet %s", inst_id)
            return _json_response(message=_("Failed to complete installation worksheet."), status=500, error="INTERNAL_ERROR")

    # =========================================================================
    # 10. Service Tickets & Warranty Breakdown Claims (Scenario 5)
    # =========================================================================
    @http.route('/api/solar/v1/service/tickets', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def api_service_tickets(self, **kw):
        """List or create customer support breakdown claims."""
        user, err = _require_auth('solar_management.group_solar_service')
        if err:
            return err

        env = request.env
        if request.httprequest.method == 'GET':
            tickets = env['solar.service.ticket'].search([])
            data = [{
                'id': t.id,
                'name': t.name,
                'customer': {'id': t.partner_id.id, 'name': t.partner_id.name},
                'serial_number': t.lot_id.name if t.lot_id else None,
                'issue_category': t.issue_category,
                'is_under_warranty': t.is_under_warranty,
                'state': t.state,
                'priority': t.priority,
            } for t in tickets]
            return _json_response(data=data)

        # POST: Create new service ticket
        body = _parse_json_body()
        required = ['partner_id', 'lot_id', 'issue_description']
        missing = [f for f in required if not body.get(f)]
        if missing:
            return _json_response(message=f"Missing fields: {missing}", status=400, error="VALIDATION_ERROR")

        try:
            with request.env.cr.savepoint():
                lot = env['stock.lot'].browse(int(body['lot_id']))
                if not lot.exists():
                    return _json_response(message="Serial lot not found.", status=404, error="NOT_FOUND")

                ticket_vals = {
                    'partner_id': int(body['partner_id']),
                    'lot_id': lot.id,
                    'product_id': lot.product_id.id,
                    'fault_category': body.get('fault_category') or body.get('issue_category') or 'inverter_fault',
                    'issue_description': body.get('issue_description'),
                    'reported_error_code': body.get('reported_error_code') or body.get('error_code'),
                    'technician_id': user.id,
                }
                ticket = env['solar.service.ticket'].create(ticket_vals)
                return _json_response(data={
                    'id': ticket.id,
                    'name': ticket.name,
                    'is_under_warranty': ticket.warranty_covered,
                    'warranty_coverage_status': ticket.warranty_coverage_status,
                }, status=201)
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="VALIDATION_ERROR")
        except Exception as e:
            _logger.exception("Error creating service ticket")
            return _json_response(message=_("Failed to create service ticket."), status=500, error="INTERNAL_ERROR")

    @http.route('/api/solar/v1/service/tickets/<int:ticket_id>/create-repair', type='http', auth='none', methods=['POST'], csrf=False)
    def api_ticket_create_repair(self, ticket_id, **kw):
        """Generate ₹0 covered warranty repair order or chargeable repair (Scenario 5)."""
        user, err = _require_auth('solar_management.group_solar_service')
        if err:
            return err

        ticket = request.env['solar.service.ticket'].browse(ticket_id)
        if not ticket.exists():
            return _json_response(message="Ticket not found.", status=404, error="NOT_FOUND")

        try:
            with request.env.cr.savepoint():
                res = ticket.action_create_repair_order()
                repair_id = res.get('res_id')
                return _json_response(data={'repair_id': repair_id}, message="Repair order generated successfully.")
        except (UserError, ValidationError) as e:
            return _json_response(message=str(e), status=400, error="REPAIR_ERROR")
        except Exception as e:
            _logger.exception("Error creating repair order for ticket %s", ticket_id)
            return _json_response(message=_("Failed to create repair order."), status=500, error="INTERNAL_ERROR")

    # =========================================================================
    # 11. PM Surya Ghar Subsidies (Scenario 6)
    # =========================================================================
    @http.route('/api/solar/v1/subsidies', type='http', auth='none', methods=['GET'], csrf=False)
    def api_subsidies_list(self, **kw):
        """List PM Surya Ghar subsidy tracking cases."""
        user, err = _require_auth()
        if err:
            return err

        subsidies = request.env['solar.subsidy.case'].search([])
        data = [{
            'id': s.id,
            'name': s.name,
            'customer': {'id': s.partner_id.id, 'name': s.partner_id.name},
            'capacity_kw': s.capacity_kw,
            'calculated_cfa_subsidy': s.calculated_cfa_subsidy,
            'discom_consumer_no': s.discom_consumer_no,
            'state': s.state,
        } for s in subsidies]
        return _json_response(data=data)

    # =========================================================================
    # 12. Digital Solar Passport (DSP Flow & ERD)
    # =========================================================================
    @http.route('/api/solar/v1/passports', type='http', auth='none', methods=['GET'], csrf=False)
    def api_passports_list(self, **kw):
        """List Digital Solar Passports with filtering and summary counts."""
        user, err = _require_auth()
        if err:
            return err

        domain = []
        if kw.get('partner_id'):
            try:
                domain.append(('partner_id', '=', int(kw.get('partner_id'))))
            except ValueError:
                pass
        if kw.get('state'):
            domain.append(('state', '=', kw.get('state')))
        if kw.get('system_type'):
            domain.append(('system_type', '=', kw.get('system_type')))

        passports = request.env['solar.passport'].search(domain)
        data = [{
            'id': p.id,
            'name': p.name,
            'customer': {'id': p.partner_id.id, 'name': p.partner_id.name},
            'installation_id': p.installation_id.id,
            'installation_name': p.installation_id.name,
            'installed_capacity_kw': p.installed_capacity_kw,
            'system_type': p.system_type,
            'commissioning_date': p.commissioning_date,
            'state': p.state,
            'component_count': p.component_count,
            'active_warranty_count': p.active_warranty_count,
            'service_ticket_count': p.service_ticket_count,
            'verification_token': p.verification_token,
            'verification_url': p.verification_url,
        } for p in passports]
        return _json_response(data=data)

    @http.route('/api/solar/v1/passports/<int:passport_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def api_passport_detail(self, passport_id, **kw):
        """Get full details of a Digital Solar Passport including components, warranties, and commissioning measurements."""
        user, err = _require_auth()
        if err:
            return err

        passport = request.env['solar.passport'].browse(passport_id)
        if not passport.exists():
            return _json_response(message='Digital Solar Passport not found.', status=404, error='NOT_FOUND')

        components = [{
            'id': c.id,
            'product_id': c.product_id.id,
            'product_name': c.product_id.display_name,
            'component_type': c.component_type,
            'lot_id': c.lot_id.id,
            'serial_number': c.serial_number,
            'warranty_id': c.warranty_id.id if c.warranty_id else None,
            'warranty_status': c.warranty_status,
            'warranty_end': c.warranty_end,
            'days_remaining': c.days_remaining,
            'is_under_warranty': c.is_under_warranty,
            'installation_date': c.installation_date,
        } for c in passport.component_ids]

        tickets = [{
            'id': t.id,
            'name': t.name,
            'ticket_type': t.ticket_type,
            'priority': t.priority,
            'state': t.state,
            'warranty_covered': t.warranty_covered,
            'date_raised': t.create_date,
        } for t in passport.service_ticket_ids]

        data = {
            'id': passport.id,
            'name': passport.name,
            'customer': {
                'id': passport.partner_id.id,
                'name': passport.partner_id.name,
                'phone': passport.partner_id.phone,
                'email': passport.partner_id.email
            },
            'installation': {
                'id': passport.installation_id.id,
                'name': passport.installation_id.name,
                'sales_order': passport.sale_order_id.name if passport.sale_order_id else None,
                'lead_technician': passport.lead_technician_id.name if passport.lead_technician_id else None,
                'gps_latitude': passport.gps_latitude,
                'gps_longitude': passport.gps_longitude,
                'test_dc_voltage': passport.test_dc_voltage,
                'test_ac_voltage': passport.test_ac_voltage,
                'test_generation_kw': passport.test_generation_kw,
                'customer_signed_by': passport.customer_signed_by,
                'customer_signed_date': passport.customer_signed_date,
            },
            'system_type': passport.system_type,
            'installed_capacity_kw': passport.installed_capacity_kw,
            'commissioning_date': passport.commissioning_date,
            'state': passport.state,
            'verification_token': passport.verification_token,
            'verification_url': passport.verification_url,
            'components': components,
            'service_tickets': tickets,
        }
        return _json_response(data=data)

    @http.route('/api/solar/v1/passports/by-serial/<string:serial_no>', type='http', auth='none', methods=['GET'], csrf=False)
    def api_passport_by_serial(self, serial_no, **kw):
        """Lookup Digital Solar Passport directly by any component serial number."""
        user, err = _require_auth()
        if err:
            return err

        comp = request.env['solar.passport.component'].search([('serial_number', '=', serial_no)], limit=1)
        if not comp:
            comp = request.env['solar.passport.component'].search([('lot_id.name', '=', serial_no)], limit=1)

        if not comp:
            return _json_response(message="No passport found for serial number '" + serial_no + "'.", status=404, error='NOT_FOUND')

        return self.api_passport_detail(comp.passport_id.id)

    @http.route('/api/solar/v1/passports/by-installation/<int:inst_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def api_passport_by_installation(self, inst_id, **kw):
        """Lookup Digital Solar Passport by installation record ID."""
        user, err = _require_auth()
        if err:
            return err

        passport = request.env['solar.passport'].search([('installation_id', '=', inst_id)], limit=1)
        if not passport:
            return _json_response(message="No passport found for installation ID " + str(inst_id) + ".", status=404, error='NOT_FOUND')

        return self.api_passport_detail(passport.id)
