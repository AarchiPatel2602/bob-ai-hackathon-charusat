import {
  User,
  Shipment,
  Disruption,
  FleetAsset,
  FleetUtilisation,
  FleetRedeploymentRecommendation,
  Alert,
  Recommendation,
  SensorReading,
  DashboardSummary,
  AIDecisionSupport
} from '../types';

const API_BASE = 'http://127.0.0.1:8000/api';

function getHeaders(): HeadersInit {
  const token = localStorage.getItem('supplyguard_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'API Request Failed';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = res.statusText;
    }
    if (res.status === 401) {
      localStorage.removeItem('supplyguard_token');
      localStorage.removeItem('supplyguard_user');
      window.dispatchEvent(new Event('auth-change'));
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(email: string, password: string):Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return handleResponse(res);
  },

  async signup(data: { email: string; password: string; full_name: string; role?: string; organization?: string }): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // Dashboard
  async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await fetch(`${API_BASE}/dashboard/summary`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getDashboardMap(): Promise<any> {
    const res = await fetch(`${API_BASE}/dashboard/map`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // Shipments
  async getShipments(params?: { search?: string; status?: string; risk_level?: string; cold_chain_only?: boolean }): Promise<Shipment[]> {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.status && params.status !== 'ALL') q.append('status', params.status);
    if (params?.risk_level && params.risk_level !== 'ALL') q.append('risk_level', params.risk_level);
    if (params?.cold_chain_only) q.append('cold_chain_only', 'true');
    const res = await fetch(`${API_BASE}/shipments?${q.toString()}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getShipment(id: number): Promise<Shipment> {
    const res = await fetch(`${API_BASE}/shipments/${id}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async createShipment(data: any): Promise<Shipment> {
    const res = await fetch(`${API_BASE}/shipments`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async updateShipment(id: number, data: any): Promise<Shipment> {
    const res = await fetch(`${API_BASE}/shipments/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async deleteShipment(id: number): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/shipments/${id}`, {
      method: 'DELETE',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  async getShipmentRoutes(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/shipments/${id}/routes`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getShipmentCarriers(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/shipments/${id}/carriers`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getShipmentFleetMatches(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/shipments/${id}/fleet-matches`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getShipmentMap(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/shipments/${id}/map`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async approveReroute(id: number, payload?: any): Promise<Shipment> {
    const res = await fetch(`${API_BASE}/shipments/${id}/approve-reroute`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload || {})
    });
    return handleResponse(res);
  },

  // Disruptions
  async getDisruptions(params?: { status?: string; severity?: string }): Promise<Disruption[]> {
    const q = new URLSearchParams();
    if (params?.status && params.status !== 'ALL') q.append('status', params.status);
    if (params?.severity && params.severity !== 'ALL') q.append('severity', params.severity);
    const res = await fetch(`${API_BASE}/disruptions?${q.toString()}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async reportDisruption(data: any): Promise<Disruption> {
    const res = await fetch(`${API_BASE}/disruptions`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async analyzeDisruption(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/disruptions/${id}/analyze`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  // Fleet
  async getFleet(params?: { status?: string; asset_type?: string; refrigerated_only?: boolean }): Promise<FleetAsset[]> {
    const q = new URLSearchParams();
    if (params?.status && params.status !== 'ALL') q.append('status', params.status);
    if (params?.asset_type && params.asset_type !== 'ALL') q.append('asset_type', params.asset_type);
    if (params?.refrigerated_only) q.append('refrigerated_only', 'true');
    const res = await fetch(`${API_BASE}/fleet?${q.toString()}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async createFleetAsset(data: any): Promise<FleetAsset> {
    const res = await fetch(`${API_BASE}/fleet`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async deleteFleetAsset(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/fleet/${id}`, {
      method: 'DELETE',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  async getFleetUtilisation(): Promise<FleetUtilisation> {
    const res = await fetch(`${API_BASE}/fleet/utilisation`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getIdleFleet(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/fleet/idle`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getFleetRecommendations(): Promise<FleetRedeploymentRecommendation[]> {
    const res = await fetch(`${API_BASE}/fleet/recommendations`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async approveFleetRedeployment(assetId: number, targetDestination = 'Mumbai'): Promise<any> {
    const res = await fetch(`${API_BASE}/fleet/recommendations/${assetId}/approve?target_destination=${encodeURIComponent(targetDestination)}`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  // Sensors & Cold Chain
  async getSensorReadings(shipmentId: number): Promise<SensorReading[]> {
    const res = await fetch(`${API_BASE}/shipments/${shipmentId}/sensors`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async simulateSensor(shipmentId: number, mode: 'normal' | 'warning' | 'critical', customTemperature?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/shipments/${shipmentId}/sensors/simulate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ mode, custom_temperature: customTemperature })
    });
    return handleResponse(res);
  },

  async getColdChainStatus(shipmentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/shipments/${shipmentId}/cold-chain-status`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // Alerts
  async getAlerts(params?: { severity?: string; is_resolved?: boolean; is_read?: boolean }): Promise<Alert[]> {
    const q = new URLSearchParams();
    if (params?.severity && params.severity !== 'ALL') q.append('severity', params.severity);
    if (params?.is_resolved !== undefined) q.append('is_resolved', String(params.is_resolved));
    if (params?.is_read !== undefined) q.append('is_read', String(params.is_read));
    const res = await fetch(`${API_BASE}/alerts?${q.toString()}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async markAlertRead(id: number): Promise<Alert> {
    const res = await fetch(`${API_BASE}/alerts/${id}/read`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  async resolveAlert(id: number): Promise<Alert> {
    const res = await fetch(`${API_BASE}/alerts/${id}/resolve`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  async approveAlertAction(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/alerts/${id}/approve`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  // Recommendations
  async getRecommendations(shipmentId?: number): Promise<Recommendation[]> {
    const q = shipmentId ? `?shipment_id=${shipmentId}` : '';
    const res = await fetch(`${API_BASE}/recommendations${q}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async approveRecommendation(id: number): Promise<Recommendation> {
    const res = await fetch(`${API_BASE}/recommendations/${id}/approve`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  // AI Decision Support & Conversational Copilot
  async getAIRecommendation(shipmentId: number): Promise<AIDecisionSupport> {
    const res = await fetch(`${API_BASE}/ai/shipment-recommendation`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ shipment_id: shipmentId })
    });
    return handleResponse(res);
  },

  async chatWithBob(query: string, shipmentId?: number): Promise<{
    answer: string;
    finding: string;
    evidence: string;
    severity: string;
    affected_shipments: string[];
    recommended_action: string;
    provider_label: string;
    is_live_ai: boolean;
    suggested_queries: string[];
  }> {
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ query, shipment_id: shipmentId })
    });
    return handleResponse(res);
  },

  // Demo
  async seedDemoData(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/seed`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  async runHackathonDemo(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/run`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse(res);
  }
};
