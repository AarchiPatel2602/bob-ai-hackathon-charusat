export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  organization: string;
  is_active: boolean;
  created_at: string;
}

export interface RoutePoint {
  id: number;
  shipment_id: number;
  sequence_order: number;
  location_name: string;
  estimated_arrival?: string;
  status: 'PASSED' | 'CURRENT' | 'PENDING';
}

export interface Shipment {
  id: number;
  shipment_identifier: string;
  user_id: number;
  origin: string;
  destination: string;
  current_location: string;
  carrier: string;
  cargo_type: string;
  cargo_description?: string;
  cargo_value: number;
  currency: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'PLANNED' | 'IN_TRANSIT' | 'DELAYED' | 'DELIVERED' | 'AT_RISK' | 'CRITICAL';
  expected_departure?: string;
  expected_delivery?: string;
  cold_chain_enabled: boolean;
  minimum_temperature?: number;
  maximum_temperature?: number;
  required_fleet_type: string;
  required_capacity: number;
  capacity_unit: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_reasons?: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  route_points: RoutePoint[];
}

export interface Disruption {
  id: number;
  name: string;
  type: string;
  location: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  start_time: string;
  expected_duration_days: number;
  description?: string;
  status: 'ACTIVE' | 'RESOLVED';
  affected_shipments_count: number;
  cargo_value_at_risk: number;
  creator_id: number;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface FleetAsset {
  id: number;
  asset_identifier: string;
  asset_type: string;
  current_location: string;
  capacity: number;
  capacity_unit: string;
  is_refrigerated: boolean;
  status: 'AVAILABLE' | 'IN_TRANSIT' | 'IDLE' | 'MAINTENANCE';
  idle_since?: string;
  current_assignment?: string;
  user_id: number;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface SensorReading {
  id: number;
  shipment_id: number;
  temperature: number;
  humidity: number;
  battery_level: number;
  location_name?: string;
  is_excursion: boolean;
  severity: 'NORMAL' | 'WARNING' | 'MAJOR' | 'CRITICAL';
  timestamp: string;
  created_at: string;
}

export interface Alert {
  id: number;
  user_id: number;
  shipment_id?: number;
  disruption_id?: number;
  fleet_asset_id?: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  alert_type: string;
  title: string;
  reason: string;
  recommended_action?: string;
  is_read: boolean;
  is_resolved: boolean;
  resolved_at?: string;
  created_at: string;
}

export interface Recommendation {
  id: number;
  shipment_id?: number;
  recommendation_type: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  reason: string;
  affected_entity: string;
  current_state: string;
  recommended_state: string;
  expected_benefit: string;
  cost_impact: number;
  time_impact_hours: number;
  risk_impact_points: number;
  details?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'APPLIED';
  approved_at?: string;
  created_at: string;
}

export interface FleetUtilisation {
  total_assets: number;
  available_assets: number;
  in_transit_assets: number;
  idle_assets: number;
  maintenance_assets: number;
  total_capacity_tons: number;
  active_capacity_tons: number;
  idle_capacity_tons: number;
  maintenance_capacity_tons: number;
  current_utilisation_pct: number;
  projected_utilisation_pct: number;
  improvement_pct: number;
}

export interface FleetRedeploymentRecommendation {
  asset_id: number;
  asset_identifier: string;
  asset_type: string;
  from_location: string;
  to_location: string;
  capacity: number;
  capacity_unit: string;
  is_refrigerated: boolean;
  reason: string;
  priority: string;
  current_utilisation_pct: number;
  projected_utilisation_pct: number;
  estimated_transit_hours: number;
  status: string;
}

export interface DashboardSummary {
  active_shipments: number;
  at_risk_shipments: number;
  critical_shipments: number;
  active_disruptions: number;
  cargo_value_at_risk: number;
  fleet_utilisation_pct: number;
  cold_chain_alerts_count: number;
  critical_attention: {
    shipment_id: number;
    shipment_identifier: string;
    origin_destination: string;
    cargo_type: string;
    cargo_value: number;
    risk_score: number;
    risk_level: string;
    reason: string;
    has_cold_chain: boolean;
    current_temp?: number;
  }[];
  recent_activity: {
    id: string;
    time_str: string;
    title: string;
    subtitle: string;
    severity: string;
    entity_type: string;
  }[];
}

export interface AIDecisionSupport {
  is_live_ai: boolean;
  provider_label: string;
  disclaimer?: string | null;
  situation_summary: string;
  recommended_action: string;
  rationale: string;
  risk_impact: {
    from_risk: number;
    to_risk: number;
  };
  time_impact: string;
  cost_impact: string;
  recommended_route: string;
  recommended_carrier: string;
  recommended_fleet: string;
  tradeoffs: string[];
  confidence_score: number;
}
