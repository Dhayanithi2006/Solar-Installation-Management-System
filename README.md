# SunPower Solutions — Solar Installation Management System

> **Odoo Hackathon — Final Round Implementation**  
> A unified Odoo-based ERP application managing the complete rooftop solar business journey from customer enquiry to 20-year warranty claims and executive profitability reporting.

---

## 1. Project Overview

SunPower Solutions is a fast-growing rooftop solar installation company completing approximately **40 projects per month** for residential homes and small industrial factories with a dedicated crew of **15 technicians**. 

The company sells ready-made systems categorized by capacity (**1 kW to 5 kW**) across two primary architectures:
1. **On-Grid Systems:** Inverter, battery charge controller, panels, safety earthing, wiring boxes, and metal mounting stands.
2. **Off-Grid Systems:** Complete On-Grid configuration plus an energy storage battery bank.

This ERP solution solves the operational headaches of lost WhatsApp enquiries, manual quotation errors, unrecorded serial numbers during warranty disputes, scattered field photographs, and obscured project margins.

---

## 2. Six Mandatory Business Scenarios

1. **Scenario 1 — The Rooftop Inquiry:** Online and direct lead capture, sales qualification, technician site survey (roof direction, tilt, shadow-free area, cable distance), and **mandatory survey approval gating** before quotation.
2. **Scenario 2 — Getting the Kit Right:** Pre-configured 1–5 kW On-Grid/Off-Grid package templates with automated Bills of Materials (BoMs), advance payment verification, order confirmation, and warehouse hand-off.
3. **Scenario 3 — Dispatch Day and Serial Numbers:** Mandatory serial scanning (`stock.lot`) for inverters, batteries, and charge controllers prior to dispatch validation, with **automatic warranty clock activation on delivery date**.
4. **Scenario 4 — On the Roof:** Mobile-friendly installation worksheet, start/end timestamps, installed capacity confirmation, power generation testing, photographic evidence, and **on-screen customer acceptance signature**.
5. **Scenario 5 — The Rainy-Season Breakdown:** Fast serial/customer lookup, automated warranty coverage check, **₹0 customer billing for in-warranty repairs**, parts and labor invoicing for out-of-warranty claims, and mandatory customer confirmation before ticket closure.
6. **Scenario 6 — The Director's Month-End:** Real-time executive dashboard featuring Today/This Week/This Month filters, material COGS, technician labor costs, **installation contribution profit**, unfinished projects, and open repair tickets.

---

## 3. Project Architecture

- **Platform:** Odoo 18.0 Community Edition (CE) Baseline (forward-compatible with Odoo 19 and Odoo 20).
- **Core Addon:** `addons/solar_management/` (100% self-contained on Community Edition with zero mandatory Enterprise dependencies).
- **Optional Extension:** `addons/solar_management_enterprise/` (Cleanly bridges to Enterprise `industry_fsm`, `helpdesk`, and `documents` if deployed on Enterprise).
- **Database:** PostgreSQL 16+ (PostgreSQL 18.6 compatible).

---

## 4. Repository Layout

```text
solar-installation-management/
├── .cursor/                         # IDE MCP integration (Google Stitch)
├── .gitignore                       # Multi-layer exclusion (virtualenvs, filestores, secrets)
├── README.md                        # Master project documentation
├── addons/                          # Custom Odoo addons
│   ├── solar_management/            # Core Community-compatible ERP addon
│   └── solar_management_enterprise/ # Optional Enterprise integration bridge
├── config/                          # Server and container configurations (odoo.conf, docker-compose)
├── docs/                            # 16-document planning baseline and architecture specification
│   ├── 01_PROJECT_SPEC.md
│   ├── 02_SYSTEM_ARCHITECTURE.md
│   ├── 03_WORKFLOW_AND_NAVIGATION.md
│   ├── 04_ODOO_MODULE_MAPPING.md
│   ├── 05_DATABASE_SCHEMA.md
│   ├── 06_API_AND_DATA_CONTRACTS.md
│   ├── 07_MODULE_DEPENDENCIES.md
│   ├── 08_DESIGN_SYSTEM.md
│   ├── 09_SCREEN_INVENTORY.md
│   ├── 10_DESIGN_TO_ROUTE_MAP.md
│   ├── 11_SECURITY_AND_ACCESS_CONTROL.md
│   ├── 12_ODOO_SETUP_AND_DEPLOYMENT.md
│   ├── 13_TESTING_STRATEGY.md
│   ├── 14_IMPLEMENTATION_TRACKER.md
│   ├── 15_INTEGRATION_AND_VALIDATION.md
│   └── 16_DEMO_SCENARIO.md
├── scripts/                         # Setup, data seeding, and deployment automation scripts
└── tests/                           # Standalone integration and regression suites
```

---

## 5. Branching & Commit Strategy

- **`master` / `main`:** Production-ready baseline, tagged per milestone (`v0.1`, `v1.0`).
- **Feature Branches:** Named per subphase:
  - `phase-1/subphase-1.2-repo-foundation`
  - `phase-1/subphase-1.3-odoo-environment`
  - `phase-1/subphase-1.4-addon-foundation`
  - ... up to `phase-5/subphase-5.5-demo-prep`
- **Conventional Commits:** Follows standard formatting: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`.

---

## 6. Implementation Roadmap (5 Phases, 25 Subphases)

1. **Phase 1 — Foundation & Odoo Environment** (Subphases 1.1 to 1.5)
2. **Phase 2 — Customer Acquisition & Sales Management** (Subphases 2.1 to 2.5)
3. **Phase 3 — Inventory & Installation Operations** (Subphases 3.1 to 3.5)
4. **Phase 4 — Warranty, After-Sales Service & Financial Management** (Subphases 4.1 to 4.5)
5. **Phase 5 — Integration, Testing & Delivery** (Subphases 5.1 to 5.5)

---

## 7. License

This project is developed under the **LGPL-3** license, conforming to Odoo Community Edition standards.

