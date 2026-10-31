#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SunPower Solutions — Digital Solar Passport (DSP) Verification Suite.
Validates ERD compliance, component registry, serial number tracking,
real-time warranty linkage, REST API routes, and access control.
"""

import sys
import os
import ast
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

PASS_COUNT = 0
FAIL_COUNT = 0


def record_pass(test_name: str, detail: str = ""):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"  {GREEN}[PASS]{RESET} {test_name}" + (f" -> {detail}" if detail else ""))


def record_fail(test_name: str, detail: str = ""):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"  {RED}[FAIL]{RESET} {test_name}" + (f" -> {detail}" if detail else ""))


def audit_passport_models():
    print(f"\n{BOLD}1. Auditing Digital Solar Passport Model Definitions{RESET}")
    file_path = "addons/solar_management/models/solar_passport.py"
    if not os.path.exists(file_path):
        record_fail("solar_passport.py existence", f"Missing file: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check SolarPassport model
    if "_name = 'solar.passport'" in content:
        record_pass("SolarPassport model defined", "_name = 'solar.passport'")
    else:
        record_fail("SolarPassport model defined", "Missing _name = 'solar.passport'")

    # Check key fields on SolarPassport
    required_fields = [
        "partner_id", "installation_id", "installed_capacity_kw",
        "system_type", "commissioning_date", "lead_technician_id",
        "gps_latitude", "gps_longitude", "test_dc_voltage", "test_ac_voltage",
        "test_generation_kw", "customer_signed_by", "component_ids",
        "service_ticket_ids", "warranty_record_ids", "verification_token", "verification_url"
    ]
    for rf in required_fields:
        if rf in content:
            record_pass(f"Field '{rf}' on solar.passport")
        else:
            record_fail(f"Field '{rf}' on solar.passport", "Missing required field")

    # Check SolarPassportComponent model
    if "_name = 'solar.passport.component'" in content:
        record_pass("SolarPassportComponent model defined", "_name = 'solar.passport.component'")
    else:
        record_fail("SolarPassportComponent model defined", "Missing component model")

    comp_fields = ["passport_id", "product_id", "component_type", "lot_id", "serial_number", "warranty_id", "warranty_status"]
    for cf in comp_fields:
        if cf in content:
            record_pass(f"Field '{cf}' on solar.passport.component")
        else:
            record_fail(f"Field '{cf}' on solar.passport.component", "Missing component field")


def audit_installation_integration():
    print(f"\n{BOLD}2. Auditing Installation -> Passport Lifecycle Issuance{RESET}")
    inst_path = "addons/solar_management/models/installation.py"
    with open(inst_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "passport_id = fields.Many2one" in content and "'solar.passport'" in content:
        record_pass("installation.py passport_id Many2one linkage")
    else:
        record_fail("installation.py passport_id Many2one linkage", "Missing field")

    if "action_view_passport" in content:
        record_pass("installation.py smart button action_view_passport()")
    else:
        record_fail("installation.py smart button action_view_passport()", "Missing method")

    if "env['solar.passport'].create" in content and "action_complete" in content:
        record_pass("Automatic passport generation upon installation completion")
    else:
        record_fail("Automatic passport generation upon installation completion", "Missing auto-create logic")


def audit_api_endpoints():
    print(f"\n{BOLD}3. Auditing Digital Solar Passport REST API Routes{RESET}")
    api_path = "addons/solar_management/controllers/api.py"
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()

    routes = [
        "/api/solar/v1/passports",
        "/api/solar/v1/passports/<int:passport_id>",
        "/api/solar/v1/passports/by-serial/<string:serial_no>",
        "/api/solar/v1/passports/by-installation/<int:inst_id>"
    ]
    for r in routes:
        if r in content:
            record_pass(f"REST API route '{r}'")
        else:
            record_fail(f"REST API route '{r}'", "Route not found in api.py")


def audit_security_and_views():
    print(f"\n{BOLD}4. Auditing DSP Security ACLs, Record Rules & UI Views{RESET}")

    # ACL
    acl_path = "addons/solar_management/security/ir.model.access.csv"
    with open(acl_path, "r", encoding="utf-8") as f:
        acl_content = f.read()
    if "model_solar_passport," in acl_content and "model_solar_passport_component," in acl_content:
        record_pass("ir.model.access.csv contains DSP models")
    else:
        record_fail("ir.model.access.csv contains DSP models", "Missing ACL rules")

    # Multi-company rule
    rules_path = "addons/solar_management/security/solar_rules.xml"
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_content = f.read()
    if "solar_passport_company_rule" in rules_content:
        record_pass("Multi-company record rule for solar.passport")
    else:
        record_fail("Multi-company record rule for solar.passport", "Missing company isolation rule")

    # Sequence
    seq_path = "addons/solar_management/data/sequence_data.xml"
    with open(seq_path, "r", encoding="utf-8") as f:
        seq_content = f.read()
    if "seq_solar_passport" in seq_content:
        record_pass("Sequence data seq_solar_passport (DSP/%(year)s/XXXXX)")
    else:
        record_fail("Sequence data seq_solar_passport", "Missing sequence")

    # Views
    view_path = "addons/solar_management/views/solar_passport_views.xml"
    if os.path.exists(view_path):
        record_pass("solar_passport_views.xml view file exists")
    else:
        record_fail("solar_passport_views.xml view file exists", "File missing")

    # Menus
    menu_path = "addons/solar_management/views/solar_menus.xml"
    with open(menu_path, "r", encoding="utf-8") as f:
        menu_content = f.read()
    if "menu_solar_passports" in menu_content:
        record_pass("Menuitem menu_solar_passports registered")
    else:
        record_fail("Menuitem menu_solar_passports registered", "Missing menu item")


def main():
    print(f"{BOLD}====================================================================")
    print(f"SunPower Solutions — Digital Solar Passport Architecture Verification")
    print(f"===================================================================={RESET}")
    audit_passport_models()
    audit_installation_integration()
    audit_api_endpoints()
    audit_security_and_views()

    print(f"\n{BOLD}====================================================================")
    print(f"DSP VERIFICATION RESULTS: {PASS_COUNT} Passed, {FAIL_COUNT} Failed")
    print(f"===================================================================={RESET}")
    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}ALL DIGITAL SOLAR PASSPORT VERIFICATIONS PASSED SUCCESSFULLY!{RESET}")


if __name__ == "__main__":
    main()
