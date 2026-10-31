# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from odoo.addons.solar_management.controllers.api import (
    SolarApiController,
    _get_cors_headers,
    _json_response,
    ALLOWED_ORIGINS
)


class TestSolarApiController(TransactionCase):
    """Automated security and functional test suite for Odoo 18 Solar JSON API."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = SolarApiController()

        # Dedicated test users for role authorization testing
        cls.sales_user = cls.env['res.users'].create({
            'name': 'API Test Sales User',
            'login': 'api_sales_user',
            'email': 'apisales@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_sales').id])],
        })

        cls.technician_user = cls.env['res.users'].create({
            'name': 'API Test Installer',
            'login': 'api_installer_user',
            'email': 'apiinstaller@example.com',
            'groups_id': [(6, 0, [cls.env.ref('solar_management.group_solar_installer').id])],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'API Test Partner',
            'phone': '+91 91234 56789',
            'email': 'apitest@example.com',
        })

    def test_01_cors_allowed_origins(self):
        """Verify strict CORS handling: allowed origin receives matched origin and credentials."""
        mock_request = MagicMock()
        mock_request.httprequest.headers = {'Origin': 'http://localhost:5173'}

        with patch('odoo.addons.solar_management.controllers.api.request', mock_request):
            headers = _get_cors_headers()
            self.assertEqual(headers.get('Access-Control-Allow-Origin'), 'http://localhost:5173')
            self.assertEqual(headers.get('Access-Control-Allow-Credentials'), 'true')
            self.assertNotEqual(headers.get('Access-Control-Allow-Origin'), '*')

    def test_02_cors_disallowed_origin_rejected(self):
        """Verify untrusted origin does NOT receive Access-Control-Allow-Origin."""
        mock_request = MagicMock()
        mock_request.httprequest.headers = {'Origin': 'http://malicious-site.example.com'}

        with patch('odoo.addons.solar_management.controllers.api.request', mock_request):
            headers = _get_cors_headers()
            self.assertNotIn('Access-Control-Allow-Origin', headers)
            self.assertNotIn('Access-Control-Allow-Credentials', headers)

    def test_03_auth_login_missing_credentials(self):
        """Login request with missing credentials must return 400 Bad Request."""
        mock_request = MagicMock()
        mock_request.httprequest.data = b'{"login": "admin"}'  # missing password
        mock_request.httprequest.headers = {}

        with patch('odoo.addons.solar_management.controllers.api.request', mock_request):
            res = self.controller.api_auth_login()
            self.assertEqual(res.status_code, 400)
            data = json.loads(res.data.decode('utf-8'))
            self.assertEqual(data.get('status'), 'error')
            self.assertEqual(data.get('error'), 'BAD_REQUEST')

    def test_04_unauthenticated_session_check_returns_401(self):
        """Accessing protected endpoint without session must return 401 Unauthorized."""
        mock_request = MagicMock()
        mock_request.session.uid = False
        mock_request.httprequest.headers = {}

        with patch('odoo.addons.solar_management.controllers.api.request', mock_request):
            res = self.controller.api_auth_session()
            self.assertEqual(res.status_code, 401)
            data = json.loads(res.data.decode('utf-8'))
            self.assertEqual(data.get('error'), 'UNAUTHORIZED')

    def test_05_role_authorization_enforcement_returns_403(self):
        """Technician trying to approve a site survey (Survey Manager role) must return 403 Forbidden."""
        mock_request = MagicMock()
        mock_request.session.uid = self.technician_user.id
        mock_request.env.user = self.technician_user
        mock_request.httprequest.headers = {}

        with patch('odoo.addons.solar_management.controllers.api.request', mock_request):
            res = self.controller.api_survey_approve(survey_id=999)
            self.assertEqual(res.status_code, 403)
            data = json.loads(res.data.decode('utf-8'))
            self.assertEqual(data.get('error'), 'FORBIDDEN')

    def test_06_crm_lead_creation_input_validation(self):
        """CRM lead creation without mandatory fields must return 400."""
        mock_request = MagicMock()
        mock_request.session.uid = self.sales_user.id
        mock_request.env.user = self.sales_user
        mock_request.httprequest.data = b'{"contact_name": "Incomplete"}'  # missing phone & capacity
        mock_request.httprequest.headers = {}

        with patch('odoo.addons.solar_management.controllers.api.request', mock_request):
            res = self.controller.api_crm_leads()
            self.assertEqual(res.status_code, 400)
            data = json.loads(res.data.decode('utf-8'))
            self.assertEqual(data.get('error'), 'VALIDATION_ERROR')

    def test_07_serial_lookup_unknown_serial_returns_404(self):
        """Serial lookup for non-existent serial must return 404 Not Found."""
        mock_request = MagicMock()
        mock_request.session.uid = self.sales_user.id
        mock_request.env.user = self.sales_user
        mock_request.env['stock.lot'].search.return_value = False
        mock_request.httprequest.headers = {}

        with patch('odoo.addons.solar_management.controllers.api.request', mock_request):
            res = self.controller.api_serial_lookup(serial_no="NON_EXISTENT_SERIAL_12345")
            self.assertEqual(res.status_code, 404)
            data = json.loads(res.data.decode('utf-8'))
            self.assertEqual(data.get('error'), 'NOT_FOUND')
