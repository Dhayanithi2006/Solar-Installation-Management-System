# 16 — Final Demonstration Scenario

**Purpose:** Provide a realistic, repeatable demonstration of the six Solar Installation Management scenarios from the supplied problem statement.

## 1. Demo objective

Show that SunPower Solutions can manage one solar customer from enquiry to warranty repair using connected Odoo records. Then show the director's operational and financial overview.

Use synthetic data only. Do not use real customer details.

## 2. Demo company and seed data

| Item | Demo value | Status |
|---|---|---|
| Company | SunPower Solutions | From problem statement |
| Customer | Arun Kumar (synthetic) | Demo-created |
| Location | Chennai (illustrative) | Demo-created |
| Requested package | 3 kW On-Grid | Scenario example |
| Subsidy interest | Yes | From enquiry scenario |
| Technician | Technician A | Synthetic employee |
| Survey approver | Survey Manager A | Synthetic user |
| Warehouse user | Warehouse A | Synthetic user |
| Sales user | Sales A | Synthetic user |
| Service user | Support A | Synthetic user |
| Serial numbers | INV-DEMO-001, BAT-DEMO-001, CC-DEMO-001 | Synthetic |

The PDF does not specify component quantities, package pricing, deposit percentage, tax treatment or charge controller warranty duration. Populate these only with clearly marked demo configuration approved by the team.

## 3. Role accounts to prepare

Create one synthetic login for each role used in the presentation:

- Sales Executive
- Survey Technician
- Survey Approver
- Warehouse Manager
- Installation Technician
- Service Agent
- Accountant
- Director

Use separate browser profiles/incognito sessions if switching users during the demo. Never display administrator credentials.

## 4. Demo script — six scenarios

### Scene 1 — Enquiry and survey

**Presenter action:** Open the public solar enquiry form and submit Arun's 3 kW On-Grid request with subsidy interest.

**Show:** CRM lead appears, is assigned to Sales, and the salesperson records roof-space, electricity-bill and grid-suitability details. Create a survey and open it as the technician. Record roof direction, tilt, cable distance and photos. Submit it and switch to the approver account.

**Expected result:** Approved survey is linked to customer/enquiry. Show that quotation action is blocked before approval and available after approval.

**Requirements:** SOL-CRM-01 to SOL-SUR-03.

### Scene 2 — Package, quotation and order

**Presenter action:** Select the configured 3 kW On-Grid package.

**Show:** Quotation template and component lines populated from the approved product/BoM configuration. Show installation service where configured. Record the customer advance/full payment in the approved demo flow and confirm the sales order.

**Expected result:** Customer/order records are linked; the warehouse picking and installation scheduling hand-off are created/available.

**Requirements:** SOL-SALE-01 to SOL-OPS-02.

### Scene 3 — Dispatch and warranty activation

**Presenter action:** Open the warehouse picking.

**Show:** Required panels/inverter/accessories, scan/enter the configured serials for serial-tracked equipment, and validate delivery.

**Expected result:** Delivery is completed; each applicable serialized unit has a warranty record with start date equal to delivery date. Show example policy settings (2-year inverter/battery and 20-year panel) and state that these are the PDF's examples, not a complete catalogue.

**Requirements:** SOL-STK-01 to SOL-WAR-02.

### Scene 4 — Installation evidence

**Presenter action:** Sign in as the installation technician and open the assigned job.

**Show:** Start work, record finish time, installed capacity, photographs, successful generation test and customer acceptance/signature. Submit/complete the installation.

**Expected result:** Completion report is linked to customer, order and delivered units. Attempting to complete without required evidence should show validation.

**Requirements:** SOL-INST-01 to SOL-INST-06.

### Scene 5 — Warranty breakdown and repair

**Presenter action:** Use a prepared synthetic support ticket for the same customer and inverter serial. For the PDF's example, simulate a claim 18 months after delivery under a 2-year policy.

**Show:** Search customer, locate exact inverter serial, open warranty record, display active warranty, assign repair and record repair outcome. Show no customer charge for covered work. Optionally show a second prepared expired-warranty case where parts and labour are charged.

**Expected result:** Ticket remains unresolved until customer confirmation is captured; then it can be closed.

**Requirements:** SOL-SRV-01 to SOL-SRV-05.

### Scene 6 — Director's month-end

**Presenter action:** Sign in as Director and open the management dashboard.

**Show:** Today/week/month filters, revenue, collected advances/payments, costs, technician hours, unfinished installations, invoice status, subsidy tracking, open repairs and installation profitability.

**Expected result:** Each KPI drills down to the source records. Explain exactly how the displayed profit is calculated and which cost categories are included.

**Requirements:** SOL-MGT-01 to SOL-MGT-06.

## 5. Demo data and timeline notes

- Use one consistent completed delivery date for the main order.
- To demonstrate an 18-month warranty claim without changing the computer clock, seed a test delivery date and test claim date in a controlled demo database, or use a prepared scenario with clearly stated simulated dates.
- Ensure the warranty calculation is based on the record's delivery date, not the actual current date at demo time.
- Keep the second expired-warranty case separate from Arun's active-warranty example.
- Mark all sample prices, quantities and cost amounts as illustrative.

## 6. Demo reset strategy

Before the final presentation:

1. Take a database and filestore backup.
2. Seed the synthetic customer, products, package BoM, users, survey and sample records.
3. Verify every login and role permission.
4. Run the complete test script once.
5. Keep a clean backup so the scenario can be restored if an action fails during rehearsal.
6. Do not reset or reseed the live demo database during the presentation unless the backup procedure has been tested.

## 7. Presentation checklist

- [ ] All six scenarios can be demonstrated without manual database edits.
- [ ] Survey approval gate is visible.
- [ ] Package components are generated from configuration.
- [ ] Serial numbers are scanned/recorded before delivery validation.
- [ ] Warranty starts on delivery date.
- [ ] Installation evidence and signature are saved.
- [ ] Support finds the exact serial and warranty status.
- [ ] Covered repair does not create a customer charge for covered work.
- [ ] Expired repair shows parts/labour charge path.
- [ ] Ticket cannot close before customer confirmation.
- [ ] Director dashboard filters work and figures reconcile.
- [ ] Demo accounts use the correct permissions.
- [ ] No real personal data, secrets or credentials are exposed.
