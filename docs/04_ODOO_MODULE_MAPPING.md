# 04 — Odoo Module Mapping

**Purpose:** Map each requirement to standard Odoo applications, configuration and custom solar functionality.

## 1. Selection principle

Use standard Odoo applications for generic business functions. Customize only the solar-specific workflow and data that standard applications do not fully express. App availability, technical module names and licensing depend on the Odoo version and edition supplied by the hackathon; verify them in the target environment before writing `__manifest__.py` dependencies.

## 2. Requirement-to-application mapping

| Requirement area | Standard Odoo capability to evaluate | Custom configuration/development |
|---|---|---|
| Website enquiries | Website form + CRM lead/opportunity creation | Map solar enquiry fields, route to team, validate required information |
| Customer tracking | Contacts + CRM | Solar-specific requirement fields if they do not fit existing lead fields |
| Sales pipeline | CRM | Configure stages, activities and assignment rules |
| Site surveys | Field Service/Project task may help schedule field visits | `solar.site.survey` model, measurements, evidence and approval gate |
| Solar packages | Products, Sales, potentially Manufacturing BoM | Configure 1–5 kW On-Grid/Off-Grid variants and correct BoMs/kit structure |
| Quotation | Sales | Server-side check that linked survey is approved; package completeness validation |
| Advance payments | Sales + Accounting | Configure payment terms/down-payment flow and readiness rule; exact percentage not specified |
| Stock and delivery | Inventory | Ensure order creates correct picking; solar-specific links where needed |
| Serial scanning | Inventory lots/serial numbers + Barcode | Require serial capture on applicable product lines and link to warranty |
| Supplier purchase | Purchase | Supplier/replenishment configuration if required |
| Technician schedule | Planning and/or Field Service | Match work to 15-person technician crew and installation assignment rules |
| Installation worksheet | Field Service worksheet/task | Capture capacity, start/end, test, pictures and customer acceptance |
| Warranty | Product/lot tracking foundation | Product-specific rule and serial-specific warranty record activated on delivery |
| Service complaint | Helpdesk | Ticket fields for installed asset/serial and customer confirmation |
| Repair | Repairs (if available) | Enforce warranty decision and covered/non-covered billing logic |
| Customer/vendor accounting | Accounting | Analytic/project linkage and solar-specific report dimensions |
| Technician time | Timesheets/Planning/Employees | Link actual technician time to installation for cost calculations |
| Subsidy paperwork | Documents/attachments | Configurable subsidy case, document checklist and status tracking |
| Management reporting | Accounting, Project, Pivot/Graph views | Installation profitability and operational dashboard combining linked records |

## 3. Proposed application groups

### Core for the expected workflow

- CRM
- Sales
- Inventory
- Barcode
- Purchase (for stock procurement visibility)
- Accounting/Invoicing
- Project and/or Field Service

### Conditional on edition, environment and implementation choice

- Website
- Manufacturing (if using formal BoMs/manufacturing app rather than a suitable kit approach)
- Planning
- Helpdesk
- Repairs
- Documents
- Sign
- Employees and Timesheets

Do not mark a module as mandatory until its availability and technical name are verified in the actual hackathon environment.

## 4. Custom addon responsibilities

Initial technical addon: `solar_management`.

| Feature | Custom implementation |
|---|---|
| Site survey | Survey model, views, submit/approve/reject methods, approval audit fields |
| Quote gating | Server-side validation on relevant quotation/order operations |
| Package policy | Solar system type/capacity configuration and package completeness checks; use Odoo products/BoMs for actual lines |
| Installation | Installation record, technician/job linkage, evidence and completion validation |
| Warranty | Warranty rule and warranty record, delivery event hook, expiry computation |
| Service | Link Helpdesk ticket and repair to serial-specific warranty; calculate covered/chargeable handling |
| Subsidy | Subsidy case/document/status model or a lighter linked checklist if sufficient |
| Management | Report views/measures and filters built from reliable linked accounting/operational data |

## 5. Standard-model extension strategy

Prefer relations to standard Odoo records over creating duplicate records:

- Customer: `res.partner`
- Lead/opportunity: CRM lead model (commonly `crm.lead`; verify on target release)
- Product: product models (`product.template` / `product.product`)
- Sales quotation/order: `sale.order` and `sale.order.line`
- Serial/lot: `stock.lot` (verify target version terminology)
- Delivery: stock picking/move/move-line records
- Vendor: `res.partner` and Purchase records
- Helpdesk ticket: target release's Helpdesk ticket model if installed
- Repair: target release's repair model if installed
- Invoice/payment: Accounting models
- Employee/time: Employees/Timesheets models if installed

Model and field names above are indicative of common Odoo technical names. Verify against the exact target release before coding.

## 6. Do not duplicate these capabilities

- Do not create a custom customer table instead of Contacts.
- Do not create a second inventory ledger.
- Do not store serial numbers only as free text on installation records; use Odoo lot/serial records.
- Do not create a parallel invoice/payment ledger.
- Do not make a custom CRM pipeline unless standard CRM cannot meet the approved workflow.
- Do not use direct database writes to bypass Odoo stock or accounting operations.

## 7. Readiness gate before final app installation

Create an environment audit listing the installed applications, version, edition, technical module names, dependencies and licenses. Then finalize module dependencies in the custom addon's manifest. Record unavailable features and the approved fallback in `12_ODOO_SETUP_AND_DEPLOYMENT.md`.
