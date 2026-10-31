# 15 — Integration and Validation Plan

**Purpose:** Confirm that the Odoo apps and custom solar addon behave as one connected ERP, not as independent screens.

## 1. Integration principles

- One customer record is shared across CRM, Sales, delivery, installation and service.
- One sales order represents the accepted commercial scope.
- One product/lot identity is used for each serialized item.
- Delivery completion is the warranty activation source event.
- Installation evidence links to the same customer/order/site and delivered products.
- Service tickets reference the original installed serial and warranty record.
- Accounting records remain the financial source of truth.

## 2. Cross-module integration matrix

| Integration | Source | Target | Expected linkage | Validation |
|---|---|---|---|---|
| Website → CRM | Enquiry form | Lead/opportunity | Source, contact, requirement | Submit sample form and inspect CRM record |
| CRM → Survey | Lead/opportunity | Site survey | Customer and originating enquiry | Create survey from lead and verify relation |
| Survey → Sales | Approved survey | Quotation/order | Matching customer, site, capacity and type | Try unapproved and approved paths |
| Sales → Inventory | Confirmed order | Picking | Correct products and quantities | Confirm order and verify picking lines |
| Sales → Planning/Field Service | Confirmed order | Installation task/job | Customer, site, package, target date | Verify one job only and correct technician |
| Inventory → Warranty | Completed delivery | Warranty records | Lot/serial, customer, order, date, policy | Validate all serialized item records |
| Planning/Field Service → Installation | Field job | Custom installation | Same source order/customer/job | Verify completed evidence is attached |
| Warranty → Helpdesk | Warranty record | Ticket | Exact serial and status | Search serial from ticket form |
| Helpdesk → Repairs | Ticket | Repair order | Ticket, serial, parts and labour | Create repair and inspect source relation |
| Repairs → Accounting | Chargeable repair | Invoice/charge | Customer, billable parts/labour | Verify covered work is not invoiced |
| Sales/Stock/Timesheets/Accounting → Dashboard | Source records | Reports | Installation analytic/reference | Reconcile test installation numbers |
| Documents → Subsidy | Attachments | Subsidy case | Customer/order and document status | Verify attachment access by role |

## 3. Automation trigger catalogue

| Trigger | Intended automation | Safeguard |
|---|---|---|
| Enquiry submitted | Create CRM lead and assign/team route | Duplicate/anti-spam handling |
| Survey submitted | Notify/queue survey approver | Required fields and evidence check |
| Survey approved | Make quote workflow eligible | Server-side state validation |
| Order confirmed | Create/activate picking and installation scheduling hand-off | Idempotent; do not duplicate records |
| Delivery completed | Create warranty record per applicable serialized item | Idempotent and policy required |
| Installation submitted | Validate completion evidence and route to review/completion | Missing evidence blocks completion |
| Service ticket serial selected | Resolve warranty status | Validate customer/serial relation |
| Repair marked completed | Prepare chargeable invoice only for non-covered work | Recompute warranty and billing basis |
| Customer confirms resolution | Allow ticket closure | Confirmation is mandatory |
| Dashboard opened/date changed | Recompute/filter metrics from source data | Metric definitions and date boundaries consistent |

## 4. Integration test scenarios

### INT-01 — One customer, one complete solar job

Create a customer enquiry, approve survey, quote a configured package, confirm order, deliver serialized items, create warranty records, complete installation with evidence and verify the final customer record links all steps.

### INT-02 — Delivery retry does not duplicate warranties

Trigger the delivery post-processing path more than once in a test. Confirm exactly one applicable warranty record exists per serial/delivery.

### INT-03 — Service claim reaches the correct warranty

Open a ticket for a customer and select the inverter serial. Verify the ticket displays the correct customer, product, delivery date and warranty state.

### INT-04 — Covered and expired repair paths differ

Use one active and one expired test warranty. Confirm the active path does not charge covered work and the expired path calculates parts and labour charges.

### INT-05 — Installation cost traceability

Verify that the installation reference can be traced to sales revenue, stock/material costs and technician time used in the chosen report definition.

### INT-06 — Access boundaries survive navigation

Open records through menus, related buttons, search, list views and direct RPC/browser calls using different roles. Confirm record rules and server-side validations remain effective.

## 5. Validation of management figures

Every KPI must have a written formula and source model before it is displayed.

| KPI | Required definition before implementation |
|---|---|
| Revenue | Posted invoiced revenue or another explicitly selected basis; do not mix quotations with revenue |
| Cash received | Posted/reconciled customer payments in the selected date range |
| Outstanding | Open receivable balance as of selected date |
| Material cost | Agreed stock valuation/COGS basis, linked to installation/order |
| Labour cost | Validated technician hours multiplied by approved cost rate, or the organization's actual labour cost source |
| Job profit | Revenue minus explicitly identified costs; label gross/contribution/net correctly |
| Unfinished work | Orders/installations not in a completed/cancelled terminal state |
| Open repairs | Tickets not closed, according to ticket state definition |
| Subsidy pending | Cases in agreed pending states |

## 6. Release validation checklist

- [ ] All cross-module links resolve to the same customer/order/product/serial.
- [ ] No duplicate pickings, installations or warranty records from retry operations.
- [ ] Survey gate is enforced in both UI and backend.
- [ ] Stock delivery remains consistent with standard Odoo stock validation.
- [ ] Warranty policy snapshot remains explainable after policy changes.
- [ ] Installation evidence and customer signature are accessible only to authorized users.
- [ ] Repair billing correctly distinguishes covered and non-covered work.
- [ ] Ticket closure requires customer confirmation.
- [ ] Dashboard values are reconciled to source records.
- [ ] The six end-to-end demo scenarios pass on the target environment.
