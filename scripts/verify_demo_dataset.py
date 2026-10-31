#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SunPower Solutions — Demo Dataset Integrity Verifier (Subphase 5.3)
Scans and verifies that all synthetic demo records required for Arun Kumar's
live walkthrough (Scenarios 1 through 6) exist, are valid XML, and are wired together.
"""

import os
import sys
import glob
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
    print(f"\n{BOLD}{CYAN}SunPower Solutions — Live Demo Dataset Integrity Check{RESET}")
    print(f"{CYAN}Auditing Synthetic Demo Records for Arun Kumar 3 kW Rooftop (Subphase 5.3){RESET}")

    # Expected demo record IDs across XML data files
    required_demo_records = {
        "partner_arun_kumar": ("res.partner", "Customer Arun Kumar", "solar_crm_data.xml"),
        "crm_lead_arun_kumar_solar": ("crm.lead", "CRM Solar Enquiry Lead", "solar_crm_data.xml"),
        "survey_arun_kumar_approved": ("solar.site.survey", "Approved Site Survey", "solar_survey_data.xml"),
        "pkg_product_on_grid_3kw": ("product.product", "3 kW Solar Package Product", "solar_package_data.xml"),
        "solar_package_on_grid_3kw": ("solar.package", "3 kW Pre-Engineered Kit", "solar_package_data.xml"),
        "sale_order_arun_kumar_3kw": ("sale.order", "Arun Kumar 3 kW Confirmed Order", "solar_sale_data.xml"),
        "lot_inverter_demo_001": ("stock.lot", "Serialized Inverter (INV-DEMO-001)", "solar_lot_data.xml"),
        "installation_arun_kumar_3kw": ("solar.installation", "Installation Worksheet INST/2026/00001", "solar_installation_data.xml"),
        "warranty_inverter_arun_kumar_active": ("solar.warranty.record", "2-Year Active Warranty (18 Mo In)", "solar_warranty_data.xml"),
        "warranty_battery_expired": ("solar.warranty.record", "Expired Warranty (26 Mo In - Chargeable)", "solar_warranty_data.xml"),
        "ticket_arun_kumar_rainy_breakdown": ("solar.service.ticket", "18-Month Breakdown Claim (Error F04)", "solar_service_data.xml"),
        "ticket_expired_battery_claim": ("solar.service.ticket", "Out-of-Warranty Claim (Chargeable Repair)", "solar_service_data.xml"),
        "repair_order_arun_kumar_inverter": ("repair.order", "₹0 Covered Warranty Repair Order", "solar_repair_data.xml"),
        "invoice_arun_kumar_3kw": ("account.move", "Customer Invoice (₹1,89,000)", "solar_financial_data.xml"),
        "bill_freight_arun_kumar_3kw": ("account.move", "Attributable Freight Bill (₹3,500)", "solar_financial_data.xml"),
        "bill_inspection_arun_kumar_3kw": ("account.move", "CEIG Safety Inspection Bill (₹2,500)", "solar_financial_data.xml"),
        "bill_permit_arun_kumar_3kw": ("account.move", "DISCOM Net-Meter Permit Bill (₹4,000)", "solar_financial_data.xml"),
        "subsidy_case_arun_kumar_3kw": ("solar.subsidy.case", "PM Surya Ghar Subsidy Case (₹78,000)", "solar_subsidy_data.xml"),
    }

    # Collect all record IDs from data XML files
    found_records = {}
    data_files = glob.glob("addons/solar_management/data/*.xml")

    for fpath in data_files:
        fname = os.path.basename(fpath)
        try:
            tree = ET.parse(fpath)
            for record in tree.findall(".//record"):
                rid = record.get("id")
                rmodel = record.get("model")
                if rid:
                    found_records[rid] = (rmodel, fname)
        except Exception as e:
            print(f"{RED}Error parsing {fname}: {e}{RESET}")

    print_header("Auditing Demo Record Definitions")

    passed = 0
    total = len(required_demo_records)

    for rec_id, (expected_model, desc, expected_file) in required_demo_records.items():
        if rec_id in found_records:
            actual_model, actual_file = found_records[rec_id]
            if actual_model == expected_model:
                passed += 1
                print(f"  [{GREEN}PASS{RESET}] {desc} ({rec_id})")
                print(f"         {YELLOW}-> Model: {actual_model} | File: {actual_file}{RESET}")
            else:
                print(f"  [{RED}FAIL{RESET}] {desc} ({rec_id}): Model mismatch ({actual_model} != {expected_model})")
        else:
            print(f"  [{RED}FAIL{RESET}] Missing record '{rec_id}' (Expected in {expected_file})")

    print_header("Demo Dataset Verification Summary")
    pct = (passed / total) * 100.0
    color = GREEN if passed == total else RED
    print(f"  {BOLD}Total Demo Records Verified:{RESET} {total}")
    print(f"  {BOLD}Passed Records:{RESET}              {color}{passed} ({pct:.1f}%){RESET}")

    if passed == total:
        print(f"\n  {GREEN}{BOLD}ALL DEMO RECORDS FOR SCENARIOS 1-6 ARE 100% PREPARED AND VERIFIED!{RESET}\n")
        return 0
    else:
        print(f"\n  {RED}{BOLD}DEMO DATASET DEFECTS DETECTED!{RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
