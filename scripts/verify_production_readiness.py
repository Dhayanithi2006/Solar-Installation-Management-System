#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SunPower Solutions — Production Deployment & Hardening Auditor (Subphase 5.4)
Audits Docker Compose definitions, Odoo production configuration, healthchecks,
volume persistence, resource constraints, backup readiness, and secret hygiene.
"""

import os
import sys
import glob
import json
import configparser

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
    print(f"\n{BOLD}{CYAN}SunPower Solutions — Production Deployment & Hardening Audit{RESET}")
    print(f"{CYAN}Auditing Containerization, Configs, Healthchecks & Backups (Subphase 5.4){RESET}")

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

    print_header("1. Docker Compose Production Configuration (config/docker-compose.yml)")
    compose_path = "config/docker-compose.yml"
    check("docker-compose.yml exists", os.path.exists(compose_path))

    with open(compose_path, 'r', encoding='utf-8') as f:
        compose_content = f.read()

    check("Service 'web' (Odoo 18.0) defined", "image: odoo:18.0" in compose_content)
    check("Service 'db' (PostgreSQL 16) defined", "image: postgres:16" in compose_content)
    check("Dependency health condition: web depends on db (service_healthy)", "condition: service_healthy" in compose_content)
    check("Web healthcheck configured (socket ping on 8069)", "healthcheck:" in compose_content and "8069" in compose_content)
    check("Database healthcheck configured (pg_isready)", "pg_isready" in compose_content)
    check("Log rotation configured (json-file, max-size 10m)", "max-size: \"10m\"" in compose_content)
    check("Isolated bridge network defined (sunpower_network)", "sunpower_network" in compose_content)
    check("Backup volume mount configured (/var/lib/odoo/backups)", "../backups:/var/lib/odoo/backups" in compose_content)

    print_header("2. Odoo Production Settings Audit (config/odoo.conf)")
    conf_path = "config/odoo.conf"
    check("odoo.conf exists", os.path.exists(conf_path))

    config = configparser.ConfigParser()
    config.read(conf_path)
    options = config['options'] if 'options' in config else {}

    check("Proxy Mode enabled (proxy_mode = True for SSL reverse proxy)", options.get('proxy_mode', '').lower() == 'true')
    check("Addons path includes /mnt/extra-addons", "/mnt/extra-addons" in options.get('addons_path', ''))
    check("CPU execution timeout configured (limit_time_cpu >= 600s)", int(options.get('limit_time_cpu', 0)) >= 600)
    check("Real execution timeout configured (limit_time_real >= 1200s)", int(options.get('limit_time_real', 0)) >= 1200)
    check("Memory limits configured (limit_memory_hard >= 2GB)", int(options.get('limit_memory_hard', 0)) >= 2147483648)
    check("Database connection pool configured (db_maxconn >= 32)", int(options.get('db_maxconn', 0)) >= 32)
    check("Local fallback configuration exists (config/odoo.local.conf on port 5000)", os.path.exists("config/odoo.local.conf"))

    print_header("3. Disaster Recovery & Backup Readiness")
    backups_dir = "backups"
    check("backups/ directory exists", os.path.isdir(backups_dir))
    backup_files = [f for f in os.listdir(backups_dir) if f.endswith('.zip')]
    check(f"Backup snapshots available ({len(backup_files)} found)", len(backup_files) >= 1, f"Snapshots: {backup_files}")

    print_header("4. Repository Hygiene & Secret Security")
    check(".gitignore exists", os.path.exists(".gitignore"))
    with open(".gitignore", 'r', encoding='utf-8') as f:
        gi_content = f.read()
    check(".gitignore blocks Python bytecode (*.pyc, __pycache__)", "*.pyc" in gi_content)
    check(".gitignore blocks log files (*.log)", "*.log" in gi_content)
    check(".gitignore blocks local environment overrides", ".env" in gi_content)

    print_header("Production Deployment Readiness Summary")
    pct = (passed_checks / total_checks) * 100.0
    color = GREEN if passed_checks == total_checks else RED
    print(f"  {BOLD}Total Hardening Checks:{RESET} {total_checks}")
    print(f"  {BOLD}Passed Checks:{RESET}          {color}{passed_checks} ({pct:.1f}%){RESET}")

    if passed_checks == total_checks:
        print(f"\n  {GREEN}{BOLD}PRODUCTION DEPLOYMENT STACK IS FULLY HARDENED, RESILIENT & READY!{RESET}\n")
        return 0
    else:
        print(f"\n  {RED}{BOLD}HARDENING DEFECTS DETECTED!{RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
