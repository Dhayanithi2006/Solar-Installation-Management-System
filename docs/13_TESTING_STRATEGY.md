# 13 — Testing Strategy

**Purpose:** Verify that each requirement works end to end and that business rules cannot be bypassed through an alternative UI/API path.

## 1. Testing layers

1. **Model/unit tests:** computed fields, constraints, state transitions, date calculations and access checks.
2. **Integration tests:** interactions between custom models and CRM, Sales, Inventory, Field Service, Helpdesk, Repairs and Accounting.
3. **UI/workflow tests:** role-based screens, buttons, validation messages and navigation.
4. **End-to-end acceptance tests:** complete customer lifecycle and all six PDF scenarios.
5. **Regression tests:** re-run critical tests after addon upgrades or module integration.

Use the test framework supported by the actual Odoo release. Browser automation can be added if the environment supports it, but backend business-rule tests are mandatory.

## 2. Acceptance test catalogue

| Test ID | Requirement | Scenario | Expected result |
|---|---|---|---|
| AT-001 | SOL-CRM-01/02 | Submit website enquiry | CRM lead is created with required customer/solar data and appears for assigned sales team |
| AT-002 | SOL-CRM-03 | Qualify enquiry | Sales records roof space, bill and grid suitability or flags missing information |
| AT-003 | SOL-SUR-01/02 | Submit site survey | Measurements, technician and photographs are stored against customer/enquiry |
| AT-004 | SOL-SUR-03 | Attempt quotation with draft/rejected survey | Server blocks quote issue/send and explains survey must be approved |
| AT-005 | SOL-SUR-03 | Approve survey as authorized manager | State changes to approved and audit fields are saved |
| AT-006 | SOL-SUR-03 | Approve as unauthorized user | Operation is denied even if invoked outside UI |
| AT-007 | SOL-SALE-01/02 | Select 3 kW On-Grid package | Correct configured package lines/components are added; no component is silently omitted |
| AT-008 | SOL-SALE-01 | Select each configured capacity/type | Correct package/BoM is selected for all approved 1–5 kW On-Grid/Off-Grid combinations |
| AT-009 | SOL-PAY-01 | Confirm readiness with no required payment | Work-start readiness is blocked according to configured payment policy |
| AT-010 | SOL-OPS-01/02 | Confirm eligible sales order | Warehouse picking and installation scheduling work item become available without duplicate creation |
| AT-011 | SOL-STK-01 | Validate serialized delivery without required serial | Validation is blocked |
| AT-012 | SOL-STK-01/02 | Deliver with valid serials | Delivery records serials against customer/order |
| AT-013 | SOL-WAR-01/02 | Complete delivery | Warranty record is created with start date equal to delivery completion date |
| AT-014 | SOL-WAR-01/02 | Reprocess delivery hook | No duplicate warranty record is created |
| AT-015 | SOL-WAR-02 | Product has no configured warranty duration | System flags policy missing; does not invent expiry |
| AT-016 | SOL-INST-01/02 | Technician starts/completes job | Actual start/end, capacity and technician are recorded |
| AT-017 | SOL-INST-03/04 | Submit installation without photos/test | Completion is blocked with clear missing-evidence message |
| AT-018 | SOL-INST-05/06 | Capture acceptance/signature | Signature/evidence is linked to installation and customer/order |
| AT-019 | SOL-SRV-01/02 | Search exact serial | Customer, product, delivery and warranty are found |
| AT-020 | SOL-SRV-03 | Repair while active warranty | Covered repair is recorded with no customer charge for covered work |
| AT-021 | SOL-SRV-04 | Repair after warranty expiry | Parts/labour charges can be recorded and billed |
| AT-022 | SOL-SRV-05 | Close ticket without confirmation | Closure is blocked |
| AT-023 | SOL-SRV-05 | Customer confirms resolution | Ticket can be closed and confirmation timestamp/user is recorded |
| AT-024 | SOL-MGT-01/02 | Review project costs | Revenue and cost components reconcile to source records |
| AT-025 | SOL-MGT-03/04 | Review subsidy and open repairs | Dashboard shows current document status and unresolved tickets |
| AT-026 | SOL-MGT-05/06 | Change date filters/export | Today/week/month totals and report export reflect the selected period |

## 3. Important boundary/negative tests

- Warranty active immediately before expiry and expired immediately after expiry according to the documented date rule.
- Delivery on month-end/leap-year boundary.
- Serial number already assigned to another customer or delivery.
- Partial delivery followed by backorder.
- Customer/site mismatch between survey and order.
- Survey approved for a different capacity/system type than the quotation.
- Order amended after survey approval.
- Product/package BoM is inactive or missing a component.
- Duplicate website submission.
- Technician submits finish time earlier than start time.
- Missing installation attachment or invalid file type/size.
- Repair replacement uses a new serial number.
- Warranty policy changed after prior delivery; existing activated warranty must preserve the applied policy terms.
- Ticket reopened after customer reports the problem is not fixed.
- User attempts to access another technician's assigned job.
- A dashboard filter excludes records outside the selected date period.

## 4. Role-based tests

Create synthetic users for each proposed role. Verify:

- Correct menus/actions are visible.
- Direct model access matches access rights and record rules.
- Unauthorized state changes fail server-side.
- Attachments are not visible to unrelated users.
- A technician sees assigned work only, subject to approved exceptions.
- Finance data is restricted.
- Directors see the intended report data but do not automatically gain operational write rights.

## 5. Financial reconciliation tests

For each sample installation, compare:

- Sales order/posted invoice revenue.
- Customer payments received and outstanding receivables.
- Stock valuation/COGS or defined material cost measure.
- Vendor bills/purchase costs where applicable.
- Technician labour cost using validated time and approved cost rate.
- Transport/other direct expenses where recorded.
- Profit measure used on the dashboard.

Do not call the result "profit" until the team documents whether it is gross profit, contribution margin or net profit and which costs/overheads/taxes are included.

## 6. Test data policy

Use synthetic customers, phone numbers, addresses, serial numbers and invoices. Make package quantities and warranty policies explicit in test fixtures. The PDF does not provide package quantities or every warranty duration, so tests must use approved configurable demo data rather than presenting invented quantities/policies as source facts.

## 7. Definition of test completion

- All critical acceptance tests pass.
- No high-severity security defects remain.
- Failed validation paths show actionable messages.
- Core workflow can be completed using role-specific accounts.
- Dashboard metrics reconcile to source records.
- Regression suite passes on the exact version/edition used for the final demo.
