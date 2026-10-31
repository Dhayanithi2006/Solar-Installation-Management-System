# 08 — Design System

**Purpose:** Define a consistent, practical Odoo user experience for office staff and field technicians.

## 1. Design direction

Use a clean, professional solar-business identity while preserving familiar Odoo interaction patterns. The goal is fast, dependable operations—not a decorative standalone dashboard that hides normal ERP functions.

The internal employee interface should remain Odoo-native. Use custom styling only where it improves hierarchy, readability or field usability and is compatible with the target Odoo asset system.

## 2. Proposed visual identity

The following are design proposals, not requirements from the problem statement.

| Token | Proposed value | Usage |
|---|---|---|
| Primary | Deep solar green `#176B45` | Primary actions and selected navigation |
| Secondary | Solar amber `#E6A23C` | Highlights and attention states |
| Neutral dark | `#24313A` | Headings/text where theme permits |
| Neutral light | `#F5F7F6` | Background surfaces |
| Success | `#23864B` | Approved, completed, active |
| Warning | `#B7791F` | Pending, attention required |
| Danger | `#C0392B` | Rejected, overdue, failed |
| Information | `#2878A8` | Informational states |

Check contrast and do not depend on color alone to communicate a state. Use text labels/icons as well.

## 3. Typography and layout

- Use the Odoo-supported font stack and theme defaults unless a brand font is approved.
- Use clear page titles and section headers.
- Keep forms grouped by business task: Customer/Site, System Requirement, Survey Measurements, Approval, Evidence.
- Prefer Odoo standard list, form, kanban, calendar and graph/pivot layouts.
- Use concise labels and help text for units (kW, degrees, metres, currency).
- Avoid wide tables on mobile; use responsive cards or focused forms where supported.

## 4. Shared interaction patterns

- Required fields are visibly marked.
- Server-side validation is authoritative; client-side hints are supplementary.
- Approval actions show the record's current state and require a rejection reason.
- Irreversible/important actions (delivery validation, warranty override, repair billing, ticket closure) show a confirmation or clear review state.
- Status badges include text, not color alone.
- Empty states explain the next action.
- Error messages explain how to fix the problem.
- Show customer, order, product and serial references prominently on field/service screens.

## 5. Role-specific design priorities

### Sales

- Fast CRM pipeline and activity visibility.
- Clear survey status and prominent reason when quotation is blocked.
- Package selector showing system type and capacity.

### Survey technician

- Mobile-first form.
- Large controls and minimal typing.
- Units shown beside measurement fields.
- Easy photograph attachment.
- Save draft and submit actions clearly separated.

### Survey approver

- Compare requested system against measurements and evidence.
- Approve/reject controls with audit information.
- Rejection reason required.

### Warehouse

- Simple picking workflow.
- Scanning-first experience.
- Highlight product, required quantity and captured serials.
- Show missing serials before validation.

### Installation technician

- Display customer/site, package, assigned crew and delivered equipment.
- Capture timestamps, photos, test confirmation and signature with as few steps as possible.
- Clear incomplete/completed status.

### Service agent

- Search by customer, serial or ticket reference.
- Warranty status and policy dates shown next to the asset.
- Clear covered vs chargeable result and reason.

### Director/accountant

- Distinguish revenue, collected cash, outstanding invoices, cost and profit.
- Provide today/week/month filters.
- Offer drill-down from aggregate figures to source orders/installations/tickets.

## 6. Core components to standardize

- Status badge/state label.
- Customer and site summary.
- Solar package summary (type, kW, key products).
- Survey measurements group.
- Evidence/photo attachment area.
- Approval panel with approver, date and reason.
- Serial-number list.
- Warranty status card.
- Installation checklist/completion panel.
- Service ticket summary.
- Date-range filter and KPI card.

Prefer standard Odoo widgets before creating custom OWL components.

## 7. Accessibility and responsive behavior

- Keyboard navigation for office users.
- Labels for form controls and meaningful action names.
- Sufficient contrast.
- Do not rely on color-only status indications.
- Mobile/tablet layouts must be tested on the actual device/browser likely used by field staff.
- Avoid controls that require hover on touch devices.

## 8. Google Stitch design guidance

Stitch should be used to explore/communicate visual design and screen layouts, not as a replacement for Odoo's actual view framework. Before implementation, map each approved design to an Odoo menu/action/view or a justified custom OWL component. Any design that cannot be implemented in the available Odoo version/edition must be revised or explicitly deferred.

## 9. Design approval checklist

- [ ] Odoo-native visual conventions retained.
- [ ] Same status language across all screens.
- [ ] Survey, delivery, installation and service screens work on mobile/tablet.
- [ ] No screen permits unauthorized actions.
- [ ] Error and empty states designed.
- [ ] KPI labels distinguish money and operational counts correctly.
- [ ] Approved Stitch screens mapped in `10_DESIGN_TO_ROUTE_MAP.md`.
