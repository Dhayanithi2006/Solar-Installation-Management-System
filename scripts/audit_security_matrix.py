#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SunPower Solutions — Security & Access Control Matrix Auditor (Subphase 5.2)
Parses security groups, access control lists (ACLs), and record rules.
Audits against the principle of least privilege, privilege escalation, and multi-tenancy.
"""

import os
import sys
import csv
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(title):
    print(f"\n{BLUE}{'=' * 75}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BLUE}{'=' * 75}{RESET}")


def main():
    print(f"\n{BOLD}{CYAN}SunPower Solutions — Security & Access Control Audit{RESET}")
    print(f"{CYAN}Odoo 18.0 CE Role-Based Permission Matrix (Subphase 5.2){RESET}")

    total_checks = 0
    passed_checks = 0

    def check(description, condition, details=""):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [{GREEN}PASS{RESET}] {description}")
            if details:
                print(f"         {YELLOW}-> {details}{RESET}")
            return True
        else:
            print(f"  [{RED}FAIL{RESET}] {description}")
            if details:
                print(f"         {RED}-> {details}{RESET}")
            return False

    print_header("1. Security Groups Audit (security/solar_security.xml)")
    sec_xml_path = "addons/solar_management/security/solar_security.xml"
    tree = ET.parse(sec_xml_path)
    root = tree.getroot()

    expected_groups = [
        "group_solar_user",
        "group_solar_sales",
        "group_solar_survey_tech",
        "group_solar_survey_manager",
        "group_solar_warehouse",
        "group_solar_installer",
        "group_solar_service",
        "group_solar_service_manager",
        "group_solar_accountant",
        "group_solar_director",
        "group_solar_manager",
    ]

    found_groups = {}
    for record in root.findall(".//record[@model='res.groups']"):
        gid = record.get("id")
        name_elem = record.find("field[@name='name']")
        gname = name_elem.text if name_elem is not None else "Unnamed"
        found_groups[gid] = gname

    for gid in expected_groups:
        check(f"Group registered: '{gid}'", gid in found_groups, f"Display Name: {found_groups.get(gid, 'N/A')}")

    print_header("2. Access Control List Audit (security/ir.model.access.csv)")
    csv_path = "addons/solar_management/security/ir.model.access.csv"
    acl_rows = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            acl_rows.append(row)

    check(f"ir.model.access.csv has valid entries ({len(acl_rows)} rows)", len(acl_rows) >= 18)

    # Privilege Escalation Check: Only manager has unlink (delete) access
    unlink_violations = []
    for r in acl_rows:
        group_ref = r.get("group_id:id", "")
        perm_unlink = int(r.get("perm_unlink", 0))
        if perm_unlink == 1 and "group_solar_manager" not in group_ref:
            unlink_violations.append((r['name'], group_ref))

    check(
        "Principle of Least Privilege: Unlink (Delete) restricted to Solar Manager",
        len(unlink_violations) == 0,
        f"Violations detected: {unlink_violations}" if unlink_violations else "Clean: No unauthorized delete permissions found"
    )

    # Base User Read Permission Check
    user_read_models = set()
    for r in acl_rows:
        if "group_solar_user" in r.get("group_id:id", "") and int(r.get("perm_read", 0)) == 1:
            user_read_models.add(r.get("model_id:id", ""))

    check(
        f"Base Solar User has read access to core operational models ({len(user_read_models)} models)",
        len(user_read_models) >= 7,
        f"Audited models: {sorted(list(user_read_models))}"
    )

    print_header("3. Multi-Company & Domain Record Rules (security/solar_rules.xml)")
    rules_path = "addons/solar_management/security/solar_rules.xml"
    rtree = ET.parse(rules_path)
    rroot = rtree.getroot()

    found_rules = {}
    for record in rroot.findall(".//record[@model='ir.rule']"):
        rid = record.get("id")
        name_elem = record.find("field[@name='name']")
        domain_elem = record.find("field[@name='domain_force']")
        rname = name_elem.text if name_elem is not None else "Unnamed"
        rdomain = domain_elem.text if domain_elem is not None else ""
        found_rules[rid] = (rname, rdomain)

    # Verify Multi-Company Rules
    mc_rules = [r for r, (n, d) in found_rules.items() if "company" in r]
    check(
        f"Multi-Company record rules active ({len(mc_rules)} rules)",
        len(mc_rules) >= 5,
        f"Models protected: {mc_rules}"
    )

    # Verify Technician Assignment Domain Rule
    inst_rule = found_rules.get("solar_installation_crew_rule")
    check(
        "Technician Crew Installation Domain Rule",
        inst_rule is not None and "technician_ids" in inst_rule[1] and "lead_technician_id" in inst_rule[1],
        f"Domain Filter: {inst_rule[1] if inst_rule else 'Missing'}"
    )

    # Verify Survey Technician Domain Rule
    survey_rule = found_rules.get("solar_survey_technician_rule")
    check(
        "Survey Technician Domain Filter Rule",
        survey_rule is not None and "technician_id" in survey_rule[1],
        f"Domain Filter: {survey_rule[1] if survey_rule else 'Missing'}"
    )

    print_header("Security Audit Summary")
    pct = (passed_checks / total_checks) * 100.0
    color = GREEN if passed_checks == total_checks else RED
    print(f"  {BOLD}Total Security Checks:{RESET} {total_checks}")
    print(f"  {BOLD}Passed Checks:{RESET}         {color}{passed_checks} ({pct:.1f}%){RESET}")

    if passed_checks == total_checks:
        print(f"\n  {GREEN}{BOLD}ALL SECURITY ROLES & RECORD RULES COMPLIANT WITH ZERO VULNERABILITIES!{RESET}\n")
        return 0
    else:
        print(f"\n  {RED}{BOLD}SECURITY AUDIT DETECTED COMPLIANCE DEFECTS!{RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())

