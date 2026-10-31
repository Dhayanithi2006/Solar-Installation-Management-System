# 06 — API and Data Contracts

**Purpose:** Define how the Odoo application and its modules exchange data. This is an internal Odoo-first project; custom external REST APIs are not assumed.

## 1. Integration principle

Use Odoo ORM model methods, relations, actions and standard Odoo interfaces for communication inside one Odoo database. Do not call the same Odoo server through HTTP from one custom module to another. Use a controller only for a genuine external/public interface, such as an enquiry form that cannot be implemented with standard Website functionality.

The exact RPC/API endpoint set varies by Odoo release. Confirm the target version's supported API and authentication model before documenting public endpoints.

## 2. Internal business contracts

| Contract ID | Producer | Consumer | Trigger | Required result |
|---|---|---|---|---|
| DC-01 Enquiry capture | Website/manual entry | CRM | Customer submits enquiry | Lead/opportunity contains contact and requirement data |
| DC-02 Survey request | CRM/Sales | Site Survey | Sales requests roof inspection | Survey record assigned to technician |
| DC-03 Survey decision | Survey approver | Sales workflow | Approve/reject action | Persist decision, user, timestamp and reason |
| DC-04 Quotation eligibility | Site Survey | Sales | Quote creation/send/confirmation | Block if linked survey is not approved |
| DC-05 Package expansion | Product/BoM | Sales/Inventory | Package selected on quote/order | Correct configured component lines/quantities |
| DC-06 Confirmed order fulfilment | Sales | Inventory + scheduling | Order confirmed | Picking and installation scheduling work item are created/available |
| DC-07 Delivery serial capture | Inventory | Warranty | Delivery validated | Exact lots/serials and completed delivery date are available |
| DC-08 Warranty activation | Inventory + Warranty rules | Warranty records | Completed delivery | Create one warranty record per relevant serialized product |
| DC-09 Installation completion | Field Service/Technician | Installation | Technician submits completion | Required evidence, test and signature validated |
| DC-10 Service eligibility | Helpdesk | Warranty | Ticket serial identified | Return active/expired/unknown status and policy basis |
| DC-11 Repair billing decision | Warranty + Repair | Accounting/Sales | Repair estimate/completion | Covered work is not customer-charged; non-covered work is billed |
| DC-12 Management reporting | Sales/Stock/Timesheets/Accounting/Service | Dashboard | User opens report | Consistent date-filtered operational and financial metrics |

## 3. Canonical data contract concepts

### 3.1 Solar enquiry

```json
{
  "customer_name": "Example Customer",
  "phone": "customer-provided phone",
  "email": "optional",
  "site_address": "customer-provided address",
  "requested_capacity_kw": 3,
  "system_type": "on_grid",
  "subsidy_interest": true,
  "monthly_electricity_bill": null,
  "roof_space_notes": null,
  "source": "website"
}
```

This is a logical illustration, not a final public API schema. Field requirements, accepted values and privacy handling must be aligned with the Odoo version and actual website form.

### 3.2 Site survey submission

```json
{
  "survey_reference": "SURVEY-REFERENCE",
  "roof_direction": "north_or_other_configured_value",
  "roof_tilt": 0,
  "cable_distance": 0,
  "shadow_free_roof_area": 0,
  "grid_suitability": "suitable_or_review_required",
  "observations": "technician notes",
  "attachment_ids": [],
  "state": "submitted"
}
```

Use explicit units for numeric measurements in the actual UI/model. The numeric values above are placeholders, not defaults.

### 3.3 Warranty record

```json
{
  "serial_or_lot_reference": "LOT-OR-SERIAL",
  "product_reference": "PRODUCT-REFERENCE",
  "customer_reference": "PARTNER-REFERENCE",
  "delivery_reference": "PICKING-REFERENCE",
  "warranty_start": "delivery completion date",
  "duration_value": 2,
  "duration_unit": "years",
  "warranty_end": "computed date",
  "status": "active"
}
```

The duration is policy-derived. Never accept a user-supplied expiry date as the source of truth when it can be computed from the delivery and policy.

### 3.4 Installation completion

```json
{
  "installation_reference": "INSTALL-REFERENCE",
  "actual_start": "datetime",
  "actual_finish": "datetime",
  "installed_capacity_kw": 3,
  "generation_confirmed": true,
  "test_notes": "technician notes",
  "photo_attachment_ids": [],
  "customer_acceptance": "captured through approved Odoo signature flow"
}
```

## 4. State and error contracts

- Use controlled selection values for business states.
- Reject an invalid transition with a user-readable validation message.
- Do not treat missing warranty policy as expired; use an explicit unknown/policy-missing state requiring review.
- Do not treat an incomplete delivery as a warranty start event.
- Do not close a ticket without a customer confirmation record.
- Do not use a generic success response if the underlying stock/accounting transaction failed.

## 5. Proposed custom controller policy

A custom controller is optional, not a prerequisite. Prefer standard Website form-to-CRM behavior if available. If a controller is needed:

- Define only the minimal required routes.
- Validate and normalize input server-side.
- Apply rate limiting/anti-spam controls appropriate to the deployment.
- Never expose internal record IDs or private customer information publicly without authorization.
- Use Odoo's supported authentication/session/CSRF protections for the route type.
- Return a stable, documented response contract.
- Log failures without logging sensitive payloads or credentials.

No third-party API endpoint is specified in the problem statement. WhatsApp, subsidy portals and payment gateways remain out of scope until their technical requirements are supplied.

## 6. File and attachment contract

- Store survey photographs, installation photographs and signatures as Odoo attachments or through the standard app's supported evidence mechanism.
- Every attachment must be linked to a customer-related business record (survey, installation, subsidy case or ticket).
- Verify that the attachment's access follows the parent record's security rules.
- Restrict file type and size according to deployment policy.

## 7. Idempotency and duplicate prevention

- Re-running a delivery post-processing hook must not create duplicate warranty records.
- Reprocessing an order-confirmation trigger must not create duplicate installation jobs or duplicate pickings.
- Repeated form submissions should be protected from accidental duplicate lead creation where feasible; do not merge distinct genuine enquiries automatically without matching rules.
- Payment posting must use Odoo's accounting/payment workflow, not a custom duplicate ledger.

## 8. Contract verification checklist

- [ ] Target Odoo API/RPC behavior confirmed for exact version.
- [ ] Standard website lead form behavior tested.
- [ ] Survey approval method tested for authorized and unauthorized users.
- [ ] Quotation gate tested at server level, not only in the UI.
- [ ] Delivery hook tested for one and multiple serialized items.
- [ ] Duplicate delivery processing tested.
- [ ] Installation attachment access tested by role.
- [ ] Warranty status calculation tested at boundary dates.
- [ ] Repair billing decision tested for covered, expired and unknown policies.
- [ ] Reporting values reconciled with underlying Odoo records.
