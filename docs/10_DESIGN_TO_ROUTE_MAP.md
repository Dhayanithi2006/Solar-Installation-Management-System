# 10 — Design-to-Route and Odoo Navigation Map

**Purpose:** Map user-facing screens/designs to Odoo menus, window actions, views and security groups.

## 1. Odoo navigation approach

Odoo is not a conventional single-page application where the project owns every URL route. Navigation is primarily built with menu items, window actions, view definitions and, where justified, website routes. The exact XML IDs and menu hierarchy must be verified against the installed Odoo release and apps.

Do not invent final XML IDs at the planning stage. Use the proposed identifiers below as documentation IDs; assign stable XML IDs during implementation.

## 2. Proposed custom menu tree

```text
Solar Operations
├── Site Surveys
│   ├── All Surveys
│   ├── My Surveys
│   └── Survey Approvals
├── Installations
│   ├── All Installations
│   ├── My Installation Jobs
│   └── Installation Reports
├── Warranty
│   ├── Warranty Records
│   └── Warranty Rules
├── Subsidy Tracking
│   ├── Subsidy Cases
│   └── Document Checklist
└── Solar Reports
    ├── Installation Profitability
    ├── Operational Overview
    └── Open Service Tickets
```

Existing applications remain accessible through their standard Odoo menus: CRM, Sales, Inventory, Purchase, Planning/Field Service, Helpdesk, Repairs, Accounting, Project and Employees/Timesheets, where installed.

## 3. Design-to-navigation mapping

| Screen ID | Odoo app/menu destination | Action/view proposal | Allowed group(s) | Notes |
|---|---|---|---|---|
| SCR-010 | Website | Website form route/page | Public visitor | Use standard form-to-CRM if possible |
| SCR-011 | CRM | CRM pipeline action | Sales | Standard Odoo view |
| SCR-012 | CRM | Lead/opportunity form action | Sales | Extend only necessary solar fields |
| SCR-020 | Solar Operations → Site Surveys | Survey action, list/kanban | Survey Manager, Admin, permitted Sales | Custom model view |
| SCR-021/022 | Solar Operations → Site Surveys / Field Service task | Survey form/worksheet | Survey Technician | Mobile-first |
| SCR-023 | Solar Operations → Survey Approvals | Survey form with approval actions | Survey Approver, Admin | Server-side role check |
| SCR-014/015 | Sales | Quotation form | Sales | Custom package/survey gate integration |
| SCR-016 | Sales | Sales order form | Sales, Operations, Admin | Standard order with related records |
| SCR-030/031/033 | Inventory | Operations → Transfers / picking | Warehouse, Inventory Manager | Standard stock views |
| SCR-032 | Inventory/Barcode | Barcode operation/picking view | Warehouse | Confirm app availability |
| SCR-034 | Inventory / Solar Operations → Warranty | Lot/serial form and traceability | Warehouse, Support, Admin | Search by serial |
| SCR-040 | Planning/Field Service | Schedule/calendar view | Planner, Operations, Technician (limited) | Standard app if installed |
| SCR-041/042 | Field Service / Solar Operations → Installations | Task/installation form | Technician, Operations | Link standard task to custom record |
| SCR-043/044 | Field Service worksheet / custom form | Completion and signature action | Technician; customer signatory as supported | Confirm signature mechanism |
| SCR-045 | Field Service / Documents | Report action | Authorized internal users/customer if portal enabled | Attachment permissions required |
| SCR-050/051 | Solar Operations → Warranty | Warranty list/form | Support, Operations, Admin | Custom record views |
| SCR-052/053 | Helpdesk | Ticket list/form | Support, Service Manager, Admin | Extend ticket with serial/warranty links |
| SCR-054 | Repairs | Repair order form | Service Technician, Support Manager | Standard app if installed |
| SCR-055 | Helpdesk | Ticket resolution action | Support, Service Manager | Require customer confirmation |
| SCR-060/061 | Accounting / Purchase | Invoice, payment, vendor bill views | Accountant, authorized Manager | Standard financial records |
| SCR-062 | Timesheets/Employees | Timesheet view | Technician (own), Manager, Accountant | Depends on installed app |
| SCR-063/064 | Solar Operations → Subsidy Tracking | Subsidy case list/form | Sales, Accountant, Admin | Custom lightweight tracker |
| SCR-070/071/072 | Solar Operations → Solar Reports | Dashboard/report actions | Director, Accountant, authorized managers | Custom report views or spreadsheet/dashboard |

## 4. Website route proposal

If a public enquiry form is not handled by standard Website functionality, the custom route may be documented during implementation as a route such as `/solar/enquiry`. This is an example only, not a committed route. Route security, anti-spam, CSRF behavior and publication settings must be checked for the selected Odoo version.

## 5. Action and navigation rules

- Opening a linked customer/order/serial should navigate to the existing Odoo record, not create a duplicate view of the same entity.
- A blocked quotation action should keep the user on the order/quotation and clearly open or link to the pending survey.
- An approval action should return to the survey record and show the new state.
- A delivery validation should return to the picking and show captured lots/serials.
- A service ticket should link to customer, serial, warranty record and repair order.
- Dashboard KPI clicks should open filtered source records matching the KPI definition.

## 6. State-aware action visibility

Button visibility is a usability aid only. Server-side methods must enforce the same rule. Examples:

| Action | Visible/enabled when | Server-side validation |
|---|---|---|
| Submit survey | Survey draft/corrected and required fields complete | Validate mandatory measurements/evidence |
| Approve survey | Submitted and user has approver group | Verify group and valid state |
| Create/send quotation | Relevant survey approved | Check linked survey state on server |
| Validate delivery | Picking ready and required serials captured | Use Odoo stock validation and serial constraints |
| Complete installation | Installation in progress and evidence complete | Validate times, test, capacity, photos/signature |
| Mark repair covered | Warranty confirmed active | Recalculate from warranty record/policy |
| Close ticket | Resolution recorded and customer confirmation captured | Enforce confirmation before close |

## 7. Mapping maintenance

When a Stitch design is approved, record its screen/project identifier, revision and owner against the relevant screen ID. If a screen changes, update this table and `SCREEN_INVENTORY.md` in the same change. Keep one authoritative mapping; do not let a design prompt invent a new workflow or role.
