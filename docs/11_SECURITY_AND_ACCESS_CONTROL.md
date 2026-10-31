# 11 — Security and Access Control

**Purpose:** Define role-based access and protection for customer, stock, warranty, service and financial records.

## 1. Security principles

- Apply least privilege: each user receives only the access required for their job.
- Enforce permissions server-side using Odoo groups, model access rights, record rules and method checks.
- Hiding a menu or button is not sufficient security.
- Preserve audit information for approvals, stock delivery, warranty changes and service decisions.
- Protect customer contact information, site addresses, photographs, signatures and financial records.
- Never commit credentials, access tokens, database passwords or real customer data to Git.

## 2. Proposed security groups

| Group | Intended users |
|---|---|
| `Solar / Administrator` | Authorized system administrators |
| `Solar / Sales User` | Sales executives |
| `Solar / Survey Technician` | Employees performing site surveys |
| `Solar / Survey Approver` | Managers authorized to approve/reject surveys |
| `Solar / Warehouse User` | Warehouse operators |
| `Solar / Installation Technician` | Field installation crew |
| `Solar / Service User` | Customer support/service agents |
| `Solar / Service Manager` | Service supervisors and repair authorization |
| `Solar / Accountant` | Finance employees |
| `Solar / Director` | Management reporting and permitted read access |

Some groups may imply standard Odoo groups. Avoid creating contradictory duplicate permissions; document the combined effective access after configuration.

## 3. Proposed permission matrix

Legend: **R** = read, **C** = create, **W** = write, **A** = approve/validate, **X** = delete (normally restricted). This is a starting proposal and must be refined to actual job duties.

| Data/action | Admin | Sales | Survey Tech | Survey Approver | Warehouse | Installer | Service | Accountant | Director |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Customers | R/W | R/W | R limited to assigned jobs | R | R limited to delivery | R limited to jobs | R | R | R |
| CRM leads | R/W | R/W | R assigned survey only | R as needed | — | — | R as needed | R as needed | R |
| Site surveys | R/W/A | R/W request/read | C/W own assigned | R/A | — | R linked job only | R as needed | — | R |
| Quotations/orders | R/W | R/W | R limited to assigned job | R as needed | R fulfilment only | R assigned job | R as needed | R | R |
| Product/stock | R/W | R | R required items | R | R/W/A stock | R assigned items | R | R | R |
| Delivery/serials | R/W | R | R assigned context | R as needed | R/W/A | R installed items | R | R | R |
| Installations | R/W | R | R assigned context | R as needed | R dispatched context | R/W own assigned | R | R | R |
| Warranty records/rules | R/W | R status only | R assigned assets | R | R serial capture context | R assigned assets | R/W status | R charge context | R |
| Service tickets/repairs | R/W | R limited | R assigned ticket if assigned | — | R parts context | R assigned repair | R/W | R billing | R |
| Invoices/payments | R/W | R limited status | — | — | — | — | R charge status | R/W/A | R read/report |
| Management reports | R | Limited sales view | Own work only | Survey view | Stock view | Own work only | Service view | R/W | R |

Do not grant directors full write access to operational records by default. Read/report access should be enough unless the business owner explicitly requests otherwise.

## 4. Record-rule recommendations

- Survey technicians: read/write only surveys assigned to them, with narrowly defined create/submit permissions.
- Survey approvers: read surveys requiring approval; approve/reject only through authorized methods.
- Installation technicians: read/write only assigned installation jobs and relevant customer/site/product context; cannot alter sales price or warranty policy.
- Warehouse users: operate stock transfers according to standard stock permissions; cannot change customer warranty terms.
- Service users: read the customer/serial/warranty information needed for a ticket; cannot edit historical delivery date or warranty rule.
- Accountants: access accounting records according to standard finance groups; no unauthorized changes to survey/installation evidence.
- Directors: read permitted business metrics and source records; no implicit access to attachments or sensitive records beyond business need.

## 5. Critical authorization checks

- Only Survey Approver/Admin may approve or reject a submitted survey.
- Only authorized Sales/Manager may issue a quotation after checking survey approval.
- Only warehouse users with stock validation rights may validate delivery.
- Only authorized admin/operations roles may change warranty policy.
- Warranty status used for billing must be computed from the record/policy, not accepted from a client-side field.
- Only service manager/authorized staff may approve exceptional charge overrides.
- Only authorized users may close tickets, and server-side validation must check customer confirmation.
- Only accountant/authorized finance manager may post invoices/payments.

## 6. Data and attachment protection

- Restrict survey photos, home/site photos, signatures and subsidy documents to users with access to the parent business record.
- Do not expose private attachments through predictable public URLs.
- Avoid putting personal data in server logs, URLs or demo screenshots unless synthetic.
- Use synthetic customer data for testing and final presentation.
- If customer portal access is enabled, ensure each customer can see only their own permitted records.

## 7. Audit trail

Record at minimum:

- Survey submitted, approved or rejected: actor, timestamp, previous/new state and rejection reason.
- Delivery validated: stock reference, product and lot/serial.
- Warranty activated/adjusted: source delivery, policy used, actor and reason for any override.
- Installation completed: submitter, times, evidence and customer acceptance.
- Repair warranty decision: serial, policy result, decision and any override reason.
- Service ticket closure: customer confirmation and closing user/time.

Use Odoo's tracking/chatter/audit capabilities where suitable, supplemented with explicit immutable event fields where needed.

## 8. Security test checklist

- [ ] Anonymous visitor can submit enquiry but cannot read customer/order data.
- [ ] Sales user cannot approve a survey unless assigned approver group.
- [ ] Technician cannot approve their own survey unless explicitly allowed by business policy.
- [ ] User cannot bypass quotation gate using RPC/direct method call.
- [ ] Warehouse user cannot edit warranty duration.
- [ ] Installer cannot access unassigned customers' private attachments.
- [ ] Service user cannot modify completed delivery or serial ownership.
- [ ] Non-accountant cannot post invoices/payments.
- [ ] Director dashboard respects permitted record visibility.
- [ ] Ticket cannot be closed without customer confirmation.
