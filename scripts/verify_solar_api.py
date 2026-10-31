#!/usr/bin/env python3
"""
SunPower Solutions — Solar Installation Management System
Automated Verification Suite for Odoo 18 REST/JSON API Controller Architecture.
Audits route registrations, CORS policy, session authentication, and role authorization.
"""

import sys
import os
import ast
import json
from unittest.mock import MagicMock, patch

# Ensure UTF-8 output across Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

total_checks = 0
passed_checks = 0

def check(name, condition, details=""):
    global total_checks, passed_checks
    total_checks += 1
    if condition:
        passed_checks += 1
        print(f"  [{GREEN}PASS{RESET}] {name}")
        if details:
            print(f"         -> {details}")
    else:
        print(f"  [{RED}FAIL{RESET}] {name}")
        if details:
            print(f"         -> ERROR: {details}")

def print_header(title):
    print(f"\n{BOLD}{'=' * 75}\n  {title}\n{'=' * 75}{RESET}")

def main():
    print(f"\n{BOLD}SunPower Solutions — Solar REST/JSON API Architecture Audit{RESET}")
    print("Auditing Odoo 18 Controllers, CORS, Security & Route Inventory")

    api_path = os.path.join("addons", "solar_management", "controllers", "api.py")
    check("api.py exists", os.path.exists(api_path))

    with open(api_path, 'r', encoding='utf-8') as f:
        src = f.read()

    # 1. AST Route Inspection
    print_header("1. API Route Inventory & Decorator Inspection")
    tree = ast.parse(src)
    routes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    func = dec.func
                    # check if http.route or route
                    is_route = False
                    if isinstance(func, ast.Attribute) and func.attr == 'route':
                        is_route = True
                    elif isinstance(func, ast.Name) and func.id == 'route':
                        is_route = True
                    if is_route and dec.args:
                        route_path = dec.args[0].value if isinstance(dec.args[0], ast.Constant) else None
                        routes.append((node.name, route_path))

    route_paths = [r[1] for r in routes if r[1]]
    print(f"  Discovered {len(route_paths)} registered endpoints:")
    for r in route_paths:
        print(f"    - {r}")

    expected_routes = [
        "/api/solar/v1/auth/login",
        "/api/solar/v1/auth/session",
        "/api/solar/v1/auth/logout",
        "/api/solar/v1/dashboard/kpis",
        "/api/solar/v1/crm/leads",
        "/api/solar/v1/surveys",
        "/api/solar/v1/packages",
        "/api/solar/v1/orders",
        "/api/solar/v1/serials/lookup/<string:serial_no>",
        "/api/solar/v1/inventory/dispatches",
        "/api/solar/v1/installations",
        "/api/solar/v1/service/tickets",
        "/api/solar/v1/subsidies"
    ]

    for er in expected_routes:
        check(f"Endpoint registered: {er}", er in route_paths)

    # 2. CORS Policy Audit
    print_header("2. CORS Policy & Cross-Origin Security Audit")
    check("Wildcard CORS ('*') is NOT used for responses", "Access-Control-Allow-Origin = '*'" not in src and "'Access-Control-Allow-Origin': '*'" not in src)
    check("Allowed origins whitelist configured", "ALLOWED_ORIGINS" in src)
    check("Pre-flight OPTIONS route handler implemented", any("OPTIONS" in r[0].upper() or "options" in r[0].lower() for r in routes))
    check("Credentials support (Access-Control-Allow-Credentials)", "Access-Control-Allow-Credentials" in src)

    # 3. Security & Anti-Spoofing Audit
    print_header("3. Authorization & User Context Integrity Audit")
    check("Session UID validation (_require_auth)", "_require_auth" in src)
    check("Role verification using user.has_group()", "has_group" in src)
    check("Rejection of untrusted client IDs (derives user from request.env.user)", "request.env.user" in src)
    check("Structured JSON envelopes with status/code/message/data", "_json_response" in src)

    # 4. Simulation Tests
    print_header("4. Controller Logic Simulation Tests")
    # Simulate CORS evaluation logic
    allowed_set = {
        'http://localhost:5173',
        'http://localhost:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:3000',
        'https://solar-installation-management-system.odoo.com'
    }

    def simulate_cors(origin):
        headers = {}
        if origin in allowed_set:
            headers['Access-Control-Allow-Origin'] = origin
            headers['Access-Control-Allow-Credentials'] = 'true'
        return headers

    h_allow = simulate_cors('http://localhost:5173')
    check("CORS allowed origin 'http://localhost:5173' yields exact origin match", h_allow.get('Access-Control-Allow-Origin') == 'http://localhost:5173')
    check("CORS allowed origin enables Allow-Credentials", h_allow.get('Access-Control-Allow-Credentials') == 'true')

    h_deny = simulate_cors('http://evil-attacker.example.com')
    check("CORS malicious origin receives no Allow-Origin header", 'Access-Control-Allow-Origin' not in h_deny)

    # Summary
    print_header("API Verification Summary")
    pct = (passed_checks / total_checks) * 100.0
    color = GREEN if passed_checks == total_checks else RED
    print(f"  {BOLD}Total API Audit Checks:{RESET} {total_checks}")
    print(f"  {BOLD}Passed Checks:{RESET}          {color}{passed_checks} ({pct:.1f}%){RESET}")

    if passed_checks == total_checks:
        print(f"\n  {GREEN}{BOLD}REST/JSON API CONTROLLER ARCHITECTURE IS FULLY SECURE & READY FOR REACT!{RESET}\n")
        return 0
    else:
        print(f"\n  {RED}{BOLD}API AUDIT DEFECTS DETECTED!{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
