# 09 — Screen Inventory

**Purpose:** Inventory the screens/views needed to complete the Solar Installation Management workflows. Screen names are conceptual; final menus/actions depend on installed Odoo applications and edition.

## 1. Shared / administration screens

| ID | Screen/view | Primary role | Purpose | Key actions |
|---|---|---|---|---|
| SCR-001 | Odoo home/app launcher | All users | Open authorized applications | Launch app |
| SCR-002 | User and role administration | Admin | Configure users/groups | Create user, assign groups |
| SCR-003 | Solar configuration | Admin | Configure system types, capacities and policies | Maintain configuration |
| SCR-004 | Product catalogue | Admin/Product Manager | Maintain solar packages and components | Create/update products |
| SCR-005 | Warranty rules | Admin/Operations Manager | Configure product warranty policies | Create/activate policy |

## 2. Sales and CRM

| ID | Screen/view | Primary role | Purpose | Key actions |
|---|---|---|---|---|
| SCR-010 | Public solar enquiry form | Customer | Submit enquiry | Submit request |
| SCR-011 | CRM pipeline | Sales Executive | Review lead/opportunity stages | Assign, qualify, schedule activity |
| SCR-012 | Lead/opportunity form | Sales Executive | Capture customer requirements | Call, update, request survey |
| SCR-013 | Customer/site summary | Sales/Support | Review customer and site information | Open related records |
| SCR-014 | Solar package selector | Sales Executive | Choose capacity and system type | Select package |
| SCR-015 | Quotation form | Sales Executive | Prepare quotation | Generate, send, revise |
| SCR-016 | Sales order/fulfilment view | Sales/Operations | Track accepted order | Confirm, monitor delivery/job |

## 3. Site survey

| ID | Screen/view | Primary role | Purpose | Key actions |
|---|---|---|---|---|
| SCR-020 | Survey list/kanban | Survey Manager | See surveys by state | Filter, assign, open |
| SCR-021 | Survey job form | Survey Technician | View assignment and site details | Start visit, save draft |
| SCR-022 | Mobile survey worksheet | Survey Technician | Record roof and grid information | Enter measurements, photos, submit |
| SCR-023 | Survey approval review | Survey Approver | Review evidence and decide | Approve/reject with reason |
| SCR-024 | Survey history | Sales/Manager | Review previous revisions and decisions | Compare, reopen/follow-up as policy allows |

## 4. Warehouse and dispatch

| ID | Screen/view | Primary role | Purpose | Key actions |
|---|---|---|---|---|
| SCR-030 | Delivery/picking list | Warehouse Manager | View orders to prepare | Open picking |
| SCR-031 | Picking detail | Warehouse Manager | Pick package components | Confirm quantities |
| SCR-032 | Serial/barcode capture | Warehouse Manager | Capture serialized units | Scan, validate, resolve mismatch |
| SCR-033 | Delivery confirmation | Warehouse Manager | Complete dispatch | Validate delivery |
| SCR-034 | Product/serial traceability | Warehouse/Support | Trace a serial to customer/order | Search serial, open history |

## 5. Installation and technician operations

| ID | Screen/view | Primary role | Purpose | Key actions |
|---|---|---|---|---|
| SCR-040 | Technician schedule | Planner/Manager | View assigned work | Assign/reschedule |
| SCR-041 | Installation job list | Installation Technician | Review assigned installations | Open job, start work |
| SCR-042 | Installation job detail | Installation Technician | View customer, package and serials | Start, update status |
| SCR-043 | Mobile completion worksheet | Installation Technician | Record actual work and test | Enter times/capacity, upload photos |
| SCR-044 | Customer acceptance/signature | Customer/Technician | Record acceptance | Sign/confirm |
| SCR-045 | Installation report | Sales/Operations/Customer as permitted | Review completion evidence | View/download report |

## 6. Warranty and service

| ID | Screen/view | Primary role | Purpose | Key actions |
|---|---|---|---|---|
| SCR-050 | Warranty record list | Service Agent/Manager | Review installed product warranties | Filter/search |
| SCR-051 | Warranty record detail | Service Agent | See serial, dates and policy | Verify status |
| SCR-052 | Helpdesk ticket list | Service Agent | Track complaints | Assign, prioritize, update |
| SCR-053 | Service ticket form | Service Agent | Record complaint and asset | Identify serial, check warranty |
| SCR-054 | Repair order/work view | Service Technician | Perform repair/replacement | Record work and parts |
| SCR-055 | Customer resolution confirmation | Service Agent/Customer | Record confirmation | Confirm and close ticket |

## 7. Finance, subsidy and reporting

| ID | Screen/view | Primary role | Purpose | Key actions |
|---|---|---|---|---|
| SCR-060 | Customer payment/invoice view | Accountant | Review customer billing/collection | Register/reconcile payment |
| SCR-061 | Vendor bills/purchases | Accountant/Purchase | Review stock purchasing costs | Validate/reconcile bill |
| SCR-062 | Technician timesheets | Manager/Accountant | Review time and labour cost | Validate time |
| SCR-063 | Subsidy case list | Sales/Accounts | Track subsidy applications | Update status, attach documents |
| SCR-064 | Subsidy case detail | Assigned employee | Maintain checklist/evidence | Upload, submit, update |
| SCR-070 | Director dashboard | Director | Review KPIs and open work | Filter, drill down, export |
| SCR-071 | Installation profitability report | Director/Accountant | Compare job revenue and costs | Filter, open job |
| SCR-072 | Open service report | Director/Service Manager | Review unresolved tickets | Filter, assign/follow up |

## 8. Minimum screen coverage by role

| Role | Must-have screens |
|---|---|
| Admin | SCR-002 to SCR-005 plus all authorized configuration |
| Sales Executive | SCR-010 to SCR-016, SCR-020/SCR-024 read access |
| Survey Technician | SCR-021, SCR-022, relevant history |
| Survey Approver | SCR-020, SCR-023, SCR-024 |
| Warehouse Manager | SCR-030 to SCR-034 |
| Installation Technician | SCR-040 to SCR-045 |
| Service Agent | SCR-034, SCR-050 to SCR-055 |
| Accountant | SCR-060 to SCR-064, SCR-071 |
| Director | SCR-070 to SCR-072 and permitted drill-downs |

## 9. Screen implementation notes

- Many screens should be provided by standard Odoo applications rather than custom-built pages.
- A custom screen is justified only for survey entry/approval, solar installation evidence, serial-specific warranty view and solar-specific reporting where standard views do not meet the workflow.
- Every screen must map to a menu/action/view and permitted groups in `10_DESIGN_TO_ROUTE_MAP.md`.
