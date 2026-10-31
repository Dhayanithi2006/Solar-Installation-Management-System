/**
 * SunPower Solutions — Solar Installation Management System
 * TypeScript Interface Definitions for React Frontend Integration
 * Corresponding to Odoo 18 REST/JSON API (/api/solar/v1)
 */

export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  code: number;
  message: string | null;
  data: T;
  error?: string;
}

export interface UserSession {
  id: number;
  name: string;
  email: string;
  login: string;
  company: {
    id: number;
    name: string;
    currency: string;
  };
  roles: string[];
  session_id?: string;
  is_manager?: boolean;
  is_installer?: boolean;
  is_surveyor?: boolean;
}

export interface DashboardKpis {
  installations: {
    total: number;
    completed: number;
    active: number;
  };
  financials: {
    total_revenue_invoiced: number;
    material_cogs: number;
    technician_labor_cost: number;
    attributable_direct_expenses: number;
    contribution_profit: number;
    contribution_profit_margin_pct: number;
    currency: string;
  };
  subsidies: {
    total_cases: number;
    total_cfa_amount: number;
  };
  support: {
    open_tickets: number;
    total_tickets: number;
  };
}

export interface CrmLead {
  id: number;
  name: string;
  partner_name?: string;
  phone: string;
  email?: string;
  requested_capacity_kw: number;
  requested_system_type: 'on_grid' | 'off_grid' | 'hybrid';
  monthly_electricity_bill: number;
  shadow_free_roof_area: number;
  subsidy_interest: boolean;
  stage?: string;
  survey_count: number;
}

export interface SiteSurvey {
  id: number;
  name: string;
  partner: {
    id: number;
    name: string;
    phone?: string;
  };
  lead_id?: number;
  technician?: {
    id: number;
    name: string;
  };
  survey_date: string;
  roof_type: 'rcc_flat' | 'sloped_tile' | 'metal_sheet' | 'other';
  roof_area_sqft?: number;
  shadow_free_area_sqft: number;
  tilt_angle?: number;
  azimuth_angle?: number;
  shading_issues?: boolean;
  shading_description?: string;
  sanctioned_load_kw?: number;
  grid_phase?: 'single_phase' | 'three_phase';
  recommended_capacity_kw: number;
  structural_integrity_confirmed?: boolean;
  feasibility_approved?: boolean;
  state: 'draft' | 'scheduled' | 'in_progress' | 'completed' | 'approved' | 'rejected';
  approval_notes?: string;
}

export interface SolarPackage {
  id: number;
  name: string;
  code: string;
  capacity_kw: number;
  system_type: 'on_grid' | 'off_grid' | 'hybrid';
  sales_price: number;
  total_cost: number;
  state: string;
  components_count: number;
}

export interface SalesOrder {
  id: number;
  name: string;
  partner: {
    id: number;
    name: string;
  };
  package?: {
    id: number;
    name: string;
  };
  amount_total: number;
  advance_amount_required: number;
  advance_amount_paid: number;
  advance_payment_status: 'not_required' | 'pending' | 'partially_paid' | 'paid';
  work_ready: boolean;
  state: 'draft' | 'sent' | 'sale' | 'done' | 'cancel';
}

export interface SerialLookup {
  serial_id: number;
  serial_number: string;
  product: {
    id: number;
    name: string;
  };
  customer?: {
    id: number;
    name: string;
  };
  installation_id?: number;
  warranty?: {
    id: number;
    name: string;
    state: 'active' | 'expired' | 'void' | 'no_warranty';
    is_valid: boolean;
    days_remaining: number;
    warranty_start?: string;
    warranty_end?: string;
  };
}

export interface InstallationJob {
  id: number;
  name: string;
  customer: {
    id: number;
    name: string;
    phone?: string;
    street?: string;
    city?: string;
  };
  sale_order?: {
    id: number;
    name: string;
  };
  scheduled_date: string;
  state: 'draft' | 'scheduled' | 'in_progress' | 'testing' | 'completed' | 'cancelled';
  power_test: {
    voltage: number;
    current: number;
    kw_output: number;
    grid_frequency: number;
  };
  photos: {
    has_roof: boolean;
    has_inverter: boolean;
    has_db: boolean;
    has_earthing: boolean;
    has_net_meter: boolean;
  };
  customer_signed_by?: string;
  has_signature: boolean;
  customer_notes?: string;
}

export interface InstallationWorksheetSubmission {
  power_test_voltage: number;
  power_test_current: number;
  power_test_kw_output: number;
  power_test_grid_frequency: number;
  photo_panels_rooftop?: string;     // Base64 string
  photo_inverter_installed?: string;  // Base64 string
  photo_wiring_db?: string;           // Base64 string
  photo_earthing_pit?: string;        // Base64 string
  photo_net_meter?: string;           // Base64 string
  test_dc_voltage?: number;
  test_ac_voltage?: number;
  gps_latitude?: number;
  gps_longitude?: number;
  customer_signature: string;         // Base64 touch signature canvas data
  customer_signed_by: string;
  customer_notes?: string;
}

export interface ServiceTicket {
  id: number;
  name: string;
  customer: {
    id: number;
    name: string;
  };
  serial_number?: string;
  issue_category: 'inverter_fault' | 'panel_damage' | 'battery_degradation' | 'wiring_issue' | 'other';
  is_under_warranty: boolean;
  state: 'new' | 'assigned' | 'in_progress' | 'repaired' | 'closed' | 'cancelled';
  priority: '0' | '1' | '2' | '3';
}

export interface SubsidyCase {
  id: number;
  name: string;
  customer: {
    id: number;
    name: string;
  };
  capacity_kw: number;
  calculated_cfa_subsidy: number;
  discom_consumer_no?: string;
  state: 'draft' | 'submitted' | 'inspection_cleared' | 'approved' | 'disbursed' | 'rejected';
}


export interface SolarPassportComponent {
  id: number;
  product_id: number;
  product_name: string;
  component_type: 'inverter' | 'battery' | 'charge_controller' | 'panel' | 'bos' | 'other';
  lot_id: number;
  serial_number: string;
  warranty_id?: number;
  warranty_status: 'active' | 'expired' | 'void' | 'no_warranty';
  warranty_end?: string;
  days_remaining?: number;
  is_under_warranty: boolean;
  installation_date: string;
}

export interface SolarPassportSummary {
  id: number;
  name: string;
  customer: {
    id: number;
    name: string;
  };
  installation_id: number;
  installation_name: string;
  installed_capacity_kw: number;
  system_type: 'on_grid' | 'off_grid' | 'hybrid';
  commissioning_date: string;
  state: 'active' | 'decommissioned';
  component_count: number;
  active_warranty_count: number;
  service_ticket_count: number;
  verification_token: string;
  verification_url: string;
}

export interface SolarPassportDetail extends SolarPassportSummary {
  customer: {
    id: number;
    name: string;
    phone?: string;
    email?: string;
  };
  installation: {
    id: number;
    name: string;
    sales_order?: string;
    lead_technician?: string;
    gps_latitude?: number;
    gps_longitude?: number;
    test_dc_voltage?: number;
    test_ac_voltage?: number;
    test_generation_kw?: number;
    customer_signed_by?: string;
    customer_signed_date?: string;
  };
  components: SolarPassportComponent[];
  service_tickets: {
    id: number;
    name: string;
    ticket_type: string;
    priority: string;
    state: string;
    warranty_covered: boolean;
    date_raised: string;
  }[];
}
