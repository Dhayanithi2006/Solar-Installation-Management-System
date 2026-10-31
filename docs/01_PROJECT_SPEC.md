# 01 — Project Specification

**Project:** Solar Installation Management System  
**Business scenario:** SunPower Solutions  
**Document status:** Initial baseline — review and approve before implementation  
**Source of requirements:** Uploaded `Solar_Installation_Management_System.pdf` (4 pages)

## 1. Purpose

Build one unified Odoo-based business platform for a growing rooftop solar company. The platform must connect a customer's journey from the first enquiry through quotation, payment, material dispatch, installation, warranty and after-sales service. It must also give management visibility into unfinished work and job profitability.

This is an ERP customization project, not a request to create a separate CRM, inventory or accounting product. Use standard Odoo applications where they fit and implement the missing solar-specific rules in custom Odoo addons.

## 2. Business context supplied by the problem statement

| Item | Given information |
|---|---|
| Company | SunPower Solutions |
| Business | Rooftop solar installation |
| Scale | Approximately 40 projects per month |
| Customers | Homes and small factories |
| Technicians | 15 |
| Product capacities | 1 kW to 5 kW |
| System types | On-Grid and Off-Grid |
| Product examples | Panels, inverters, batteries, charge controllers, connectors, wires, stands and safety components |
| Services | Installation, fitting and testing at the customer's site |

The PDF describes an On-Grid package containing an inverter, wiring boxes, battery charge controller, panels, safety earthing and metal stands. The Off-Grid package contains the On-Grid components plus a large battery for energy storage. The PDF also lists a Solar Panel Set (hardware) and Installation (service).

## 3. Current problems

1. Enquiries arrive through WhatsApp, calls and web forms and can be lost.
2. Quotations are typed manually and components can be missed.
3. Product serial numbers are written on paper and may be unavailable during warranty claims.
4. Site work is recorded in registers and photographs are scattered across technicians' phones.
5. Revenue and job margins are not clearly visible.

## 4. Project objectives

- Capture and track every customer enquiry.
- Qualify enquiries and coordinate site surveys.
- Prevent quotation issuance until the required site survey is approved.
- Generate quotations from configured solar packages and their component lists.
- Record customer advances or full payments before work starts.
- Connect confirmed orders to warehouse preparation and technician scheduling.
- Track serialized equipment through delivery to the relevant customer and installation.
- Start product warranty periods automatically on delivery.
- Capture installation times, installed system capacity, photographs, test result and customer acceptance/signature.
- Resolve service complaints using the exact installed serial number and warranty status.
- Calculate covered versus chargeable repair costs.
- Give the director time-filtered operational and financial visibility, including profit per installation.
- Track subsidy paperwork and technician payments.

## 5. Scope and requirement baseline

The following IDs will be used in the other documents and in tests.

### Scenario 1 — Rooftop enquiry and site survey

| ID | Requirement |
|---|---|
| SOL-CRM-01 | Capture customer name, phone, address and solar requirement from an enquiry form or employee entry. |
| SOL-CRM-02 | Route the enquiry to the sales team so it can be assigned and followed up. |
| SOL-CRM-03 | Record the customer's shadow-free roof-space information, monthly electricity bill and grid suitability. |
| SOL-SUR-01 | Allow a technician to record roof direction, tilt and cable distance during a site visit. |
| SOL-SUR-02 | Store survey observations and supporting photographs against the customer/enquiry. |
| SOL-SUR-03 | Require an authorised survey approval before a customer quotation can be issued. Rejected surveys must be returned for correction or follow-up. |

### Scenario 2 — Correct package, quotation, payment and internal hand-off

| ID | Requirement |
|---|---|
| SOL-SALE-01 | Provide reusable quotation templates/packages for system capacities from 1 kW to 5 kW and for On-Grid/Off-Grid systems. |
| SOL-SALE-02 | Derive the exact component list from the selected package so sales staff do not need to remember every small part. |
| SOL-SALE-03 | Include the relevant hardware and installation service in the quotation where applicable. |
| SOL-PAY-01 | Record an advance payment or full payment before work starts. |
| SOL-OPS-01 | Once an order is confirmed, make the warehouse picking/packing requirement available. |
| SOL-OPS-02 | Once an order is confirmed, make the installation job available for crew scheduling. |

### Scenario 3 — Dispatch and serial traceability

| ID | Requirement |
|---|---|
| SOL-STK-01 | Require a serial number to be scanned/recorded for each serialized inverter, battery and charge controller before dispatch. |
| SOL-STK-02 | Link each delivered serial-numbered unit to the delivery, customer and relevant installation/order. |
| SOL-WAR-01 | Start each product's warranty automatically when delivery is completed. |
| SOL-WAR-02 | Support product-specific warranty durations. The PDF gives examples of 2 years for an inverter or battery and 20 years for solar panels. |

### Scenario 4 — Installation evidence and customer acceptance

| ID | Requirement |
|---|---|
| SOL-INST-01 | Provide a simple mobile/tablet-friendly form for the installation crew. |
| SOL-INST-02 | Record work start time, finish time and installed system size. |
| SOL-INST-03 | Upload photographs of the completed roof/installation. |
| SOL-INST-04 | Record that the system was tested and power generation was confirmed. |
| SOL-INST-05 | Capture the homeowner's on-screen acceptance/signature. |
| SOL-INST-06 | Keep the installation record and evidence connected to the customer and installed equipment. |

### Scenario 5 — Breakdown, warranty check and service ticket

| ID | Requirement |
|---|---|
| SOL-SRV-01 | Allow support staff to find the customer, installed system and exact faulty product serial number quickly. |
| SOL-SRV-02 | Display whether the identified serial number is under warranty. |
| SOL-SRV-03 | For a covered repair/replacement, charge the customer nothing for the covered work. |
| SOL-SRV-04 | For an out-of-warranty repair, calculate/record parts and labour charges and bill the customer. |
| SOL-SRV-05 | Track the complaint as a ticket until the customer confirms the issue is resolved. |

### Scenario 6 — Director's month-end

| ID | Requirement |
|---|---|
| SOL-MGT-01 | Show installations that made a profit and installations that made a loss. |
| SOL-MGT-02 | Show advance payments, stock purchases, technician hours and unfinished customer work. |
| SOL-MGT-03 | Track invoices to be sent, subsidy paperwork and technician payments. |
| SOL-MGT-04 | Show open repairs/service tickets. |
| SOL-MGT-05 | Provide today, this-week and this-month views for key management information. |
| SOL-MGT-06 | Allow reports/numbers to be shared when required. |

## 6. Proposed user roles

These roles are implementation roles inferred from the workflows; the PDF does not prescribe formal job titles or an exact permission matrix.

- System Administrator
- Sales Executive
- Survey Technician
- Survey Approver / Survey Manager
- Warehouse Manager
- Installation Technician
- Service Agent
- Accountant
- Director / Management

See `11_SECURITY_AND_ACCESS_CONTROL.md` for the proposed permissions.

## 7. In scope

- Odoo configuration and custom addons required for the six scenarios.
- Customer and enquiry management.
- Site survey and approval.
- Solar package and component configuration.
- Quotations, sales orders and payment recording.
- Stock picking, serial tracking and delivery.
- Technician planning and installation records.
- Warranty records and warranty validation.
- Helpdesk/service tickets and repair charging rules.
- Accounting/project-cost data needed for installation profitability.
- Subsidy-document status tracking (not government portal integration unless later required).
- Role-based access, auditability and scenario-based testing.

## 8. Out of scope unless the hackathon rules or later approval require them

- Building a separate React/Next.js frontend or FastAPI backend.
- Building a separate mobile app; first use Odoo's responsive interface and suitable Field Service/worksheet capabilities.
- AI/ML prediction, computer vision roof analysis or chatbot functionality.
- Live government subsidy API integration.
- Live WhatsApp/SMS gateway integration.
- IoT monitoring of solar generation.
- Payment gateway integration beyond recording/reconciling payments in Odoo.
- Full manufacturer warranty claim integration.

These may be considered later only after the six required scenarios work end to end.

## 9. Business rules to preserve

1. A quotation must not be sent before the site survey is approved.
2. The package's configured bill of materials/component list drives the required materials.
3. A customer advance or full payment is expected before work starts; exact percentage/terms are configurable because the PDF does not state them.
4. Confirmed orders must lead to warehouse preparation and crew scheduling.
5. Required serial numbers must be captured before dispatch validation.
6. Warranty starts on the actual delivery completion date, not quotation date or installation date.
7. Warranty period is maintained per product/policy. The PDF's examples are not necessarily a complete warranty catalogue; charge controller duration is not specified.
8. Installation completion evidence includes start/end time, system size, photographs, test confirmation and customer signature.
9. Covered warranty repairs/replacements carry no customer charge for the covered work.
10. Non-covered repairs must include parts and labour charges.
11. A service ticket remains open until customer confirmation of resolution.
12. Management must distinguish revenue, amounts received, costs, outstanding receivables and profit.

## 10. Non-functional requirements (proposed quality requirements)

- Role-based access and least-privilege permissions.
- Data integrity for orders, serial numbers, delivery and warranty relationships.
- Audit trail for approvals, delivery, warranty changes and repair decisions.
- Responsive technician workflow usable on a phone/tablet.
- Clear validation messages and recoverable error handling.
- Maintainable Odoo-native implementation with minimal external dependencies.
- Automated tests for critical business rules.
- Backup and deployment procedure appropriate to the chosen environment.

These are engineering recommendations, not explicit statements from the PDF.

## 11. Open decisions — do not silently assume

| Decision | Current status | Required action |
|---|---|---|
| Odoo version | Unknown | Inspect hackathon environment and lock exact version. |
| Odoo edition/hosting | Unknown | Confirm Community/Enterprise and whether Odoo.sh or a supplied server is available. |
| Python/PostgreSQL versions | Unknown | Use versions supported by the selected Odoo release. |
| Warranty duration for charge controller and other accessories | Not specified | Obtain business policy or make configurable. |
| Exact quantities in each 1–5 kW package | Not specified | Configure from approved engineering/product data. |
| Deposit percentage/payment terms | Not specified | Make configurable; do not hard-code. |
| Subsidy scheme fields/documents | Not specified | Track configurable documents/status until official checklist is supplied. |
| Signature method/legal requirements | Not specified | Confirm whether Odoo Sign or Field Service customer signature is acceptable for the demo. |
| Cost allocation/overhead rules | Not specified | Agree on direct-cost and overhead calculation before claiming net profit. |
| External integrations | Not specified | Exclude until credentials/API requirements are supplied. |

## 12. Definition of MVP completion

The MVP is complete only when a test user can execute the complete customer lifecycle—from enquiry through survey approval, quotation, payment, serialized delivery, installation, warranty activation, service ticket and management reporting—without manually recreating data between departments. Each of the six scenarios must have passing acceptance tests documented in `13_TESTING_STRATEGY.md`.
