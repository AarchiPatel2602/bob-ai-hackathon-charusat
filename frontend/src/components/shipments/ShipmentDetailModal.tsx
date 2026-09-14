import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { Shipment, AIDecisionSupport, SensorReading } from '../../types';
import { api } from '../../services/api';
import { RiskBadge } from '../common/RiskBadge';
import { StatusBadge } from '../common/StatusBadge';
import { ShipmentMap } from '../map/ShipmentMap';
import { 
  ThermometerSnowflake, 
  MapPin, 
  Truck, 
  Compass, 
  DollarSign, 
  Clock, 
  ShieldAlert, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  Play,
  RotateCcw,
  ArrowRight,
  Navigation,
  Check,
  Eye,
  EyeOff
} from 'lucide-react';

interface ShipmentDetailModalProps {
  shipmentId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated: () => void;
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const ShipmentDetailModal: React.FC<ShipmentDetailModalProps> = ({
  shipmentId,
  isOpen,
  onClose,
  onUpdated,
  onShowToast
}) => {
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'coldchain' | 'routes' | 'carriers' | 'fleet' | 'ai'>('overview');
  const [isLoading, setIsLoading] = useState(false);

  // Map & Route Planning State
  const [mapData, setMapData] = useState<any>(null);
  const [selectedPreviewRoute, setSelectedPreviewRoute] = useState<any>(null);
  const [isApproving, setIsApproving] = useState(false);

  // Engines state
  const [coldChainData, setColdChainData] = useState<any>(null);
  const [routeAlternatives, setRouteAlternatives] = useState<any[]>([]);
  const [carrierAlternatives, setCarrierAlternatives] = useState<any[]>([]);
  const [fleetMatches, setFleetMatches] = useState<any[]>([]);
  const [aiDecision, setAiDecision] = useState<AIDecisionSupport | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Live simulation ticker
  const [isLiveSimulating, setIsLiveSimulating] = useState(false);

  const fetchDetails = async (id: number) => {
    setIsLoading(true);
    try {
      // Authoritative parallel fetch: database is single source of truth
      const [s, mMap, rRes, cRes, fRes] = await Promise.all([
        api.getShipment(id),
        api.getShipmentMap(id).catch(() => null),
        api.getShipmentRoutes(id).catch(() => ({ alternatives: [] })),
        api.getShipmentCarriers(id).catch(() => ({ alternatives: [] })),
        api.getShipmentFleetMatches(id).catch(() => ({ matches: [] }))
      ]);

      setShipment(s);
      setMapData(mMap);
      const alts = (mMap?.alternative_routes && mMap.alternative_routes.length > 0)
        ? mMap.alternative_routes
        : (rRes.alternatives || []);
      setRouteAlternatives(alts);
      setCarrierAlternatives(cRes.alternatives || []);
      setFleetMatches(fRes.matches || []);

      if (s.cold_chain_enabled) {
        const cc = await api.getColdChainStatus(id).catch(() => null);
        setColdChainData(cc);
      }
    } catch (err: any) {
      onShowToast(`Failed to load shipment details: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (shipmentId && isOpen) {
      // Immediately clear stale state so previous shipment is not shown
      setShipment(null);
      setMapData(null);
      setSelectedPreviewRoute(null);
      fetchDetails(shipmentId);
    } else {
      setIsLiveSimulating(false);
      setShipment(null);
      setMapData(null);
      setSelectedPreviewRoute(null);
    }
  }, [shipmentId, isOpen]);

  // Live simulation ticker effect
  useEffect(() => {
    let interval: any;
    if (isLiveSimulating && shipmentId) {
      let step = 0;
      const stepTemps = [5.5, 6.4, 7.8, 8.6, 9.4, 10.2];
      interval = setInterval(async () => {
        const temp = stepTemps[step % stepTemps.length];
        try {
          await api.simulateSensor(shipmentId, 'critical', temp);
          const [sUpdated, ccUpdated, mMapUpdated] = await Promise.all([
            api.getShipment(shipmentId),
            api.getColdChainStatus(shipmentId),
            api.getShipmentMap(shipmentId)
          ]);
          setShipment(sUpdated);
          setColdChainData(ccUpdated);
          setMapData(mMapUpdated);
          onUpdated();
        } catch {}
        step++;
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isLiveSimulating, shipmentId]);

  const handleSimulate = async (mode: 'normal' | 'warning' | 'critical') => {
    if (!shipment) return;
    try {
      const res = await api.simulateSensor(shipment.id, mode);
      onShowToast(`Telemetry updated to ${mode.toUpperCase()} (Current: ${res.latest_temperature}°C, Risk: ${res.updated_risk_score}/100)`, 'info');
      const [sUpdated, ccUpdated, mMapUpdated] = await Promise.all([
        api.getShipment(shipment.id),
        api.getColdChainStatus(shipment.id),
        api.getShipmentMap(shipment.id)
      ]);
      setShipment(sUpdated);
      setColdChainData(ccUpdated);
      setMapData(mMapUpdated);
      onUpdated();
    } catch (err: any) {
      onShowToast(`Simulation error: ${err.message}`, 'error');
    }
  };

  const handleFetchAi = async () => {
    if (!shipment) return;
    setIsAiLoading(true);
    try {
      const res = await api.getAIRecommendation(shipment.id);
      setAiDecision(res);
    } catch (err: any) {
      onShowToast(`AI service error: ${err.message}`, 'error');
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleApproveRoute = async (route: any) => {
    if (!shipment) return;
    setIsApproving(true);
    try {
      // Deterministically persist the approved route to the database
      await api.approveReroute(shipment.id, {
        waypoints: route.waypoints,
        route_id: route.id,
        route_name: route.name,
        projected_risk_score: route.projected_risk_score
      });
      onShowToast(`Reroute approved: Active corridor diverted via ${route.name}. Operational state persisted.`, 'success');
      await fetchDetails(shipment.id);
      setSelectedPreviewRoute(null);
      onUpdated();
    } catch (err: any) {
      onShowToast(`Approval error: ${err.message}`, 'error');
    } finally {
      setIsApproving(false);
    }
  };

  const isRouteApproved = (alt: any): boolean => {
    if (!shipment || !shipment.route_points || shipment.route_points.length === 0) return false;
    const currentLocs = shipment.route_points.map(p => p.location_name.toLowerCase());
    if (alt.waypoints && alt.waypoints.length > 2) {
      const midPoints = alt.waypoints.slice(1, -1).map((w: string) => w.toLowerCase());
      return midPoints.some((m: string) => currentLocs.some(c => c.includes(m) || m.includes(c)));
    }
    return false;
  };

  if (!isOpen) return null;

  if (isLoading && !shipment) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title="Loading Shipment Details..." maxWidth="5xl">
        <div className="p-12 flex flex-col items-center justify-center space-y-3 text-slate-400">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-semibold">Retrieving authoritative shipment data from control tower...</p>
        </div>
      </Modal>
    );
  }

  if (!shipment) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${shipment.shipment_identifier} — ${shipment.cargo_type}`}
      subtitle={`${shipment.origin} → ${shipment.destination} • Consignment Value: $${shipment.cargo_value.toLocaleString()} USD`}
      maxWidth="5xl"
    >
      {/* Top Tabs */}
      <div className="flex border-b border-slate-800 -mt-2 pb-2 gap-2 overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview & Risk', icon: ShieldAlert },
          { id: 'coldchain', label: 'Cold-Chain IoT', icon: ThermometerSnowflake, badge: shipment.cold_chain_enabled },
          { id: 'routes', label: 'Alternative Routes', icon: Compass, count: routeAlternatives.length },
          { id: 'carriers', label: 'Carrier Ranking', icon: Truck, count: carrierAlternatives.length },
          { id: 'fleet', label: 'Fleet Matching', icon: Truck, count: fleetMatches.length },
          { id: 'ai', label: 'Bob / AI Assistant', icon: Sparkles }
        ].map(tab => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as any);
                if (tab.id === 'ai' && !aiDecision) handleFetchAi();
              }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                active
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview & Risk */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metric Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Risk Score</span>
              <div className="mt-1 flex items-center gap-2">
                <RiskBadge score={shipment.risk_score} level={shipment.risk_level} />
              </div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Status</span>
              <div className="mt-1">
                <StatusBadge status={shipment.status} />
              </div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Assigned Carrier</span>
              <div className="mt-1 font-semibold text-xs text-slate-200 truncate">{shipment.carrier}</div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Current Position</span>
              <div className="mt-1 font-semibold text-xs text-blue-400 truncate">{shipment.current_location}</div>
            </div>
          </div>

          {/* Interactive Map & Corridor Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Left Column: Corridor Stepper & Risk Assessment */}
            <div className="space-y-4">
              {/* Route Points Stepper */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-blue-400" />
                  <span>Active Transit Corridor</span>
                </h4>
                <div className="flex flex-col gap-2 pt-1 max-h-48 overflow-y-auto pr-1">
                  {shipment.route_points.map((pt, idx) => (
                    <div key={pt.id || idx} className="flex items-center gap-3">
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-mono shrink-0 ${
                        pt.status === 'CURRENT'
                          ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                          : pt.status === 'PASSED'
                          ? 'bg-emerald-800 text-emerald-200'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}>
                        {pt.sequence_order}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs font-semibold truncate ${pt.status === 'CURRENT' ? 'text-blue-400' : 'text-slate-300'}`}>
                          {pt.location_name}
                        </p>
                        <span className="text-[10px] text-slate-500 uppercase">{pt.status || 'PENDING'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risk Breakdown */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Deterministic Risk Assessment</h4>
                  <span className="text-xs font-mono font-bold text-slate-400">{shipment.risk_score} / 100</span>
                </div>

                <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex">
                  <div
                    className={`h-full transition-all duration-500 ${
                      shipment.risk_score >= 81 ? 'bg-rose-500' : shipment.risk_score >= 61 ? 'bg-orange-500' : shipment.risk_score >= 31 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${shipment.risk_score}%` }}
                  />
                </div>

                <div className="space-y-1 pt-1 max-h-32 overflow-y-auto">
                  <span className="text-[11px] font-semibold text-slate-400">Identified Risk Drivers:</span>
                  {shipment.risk_reasons ? (
                    shipment.risk_reasons.split('\n').map((r, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="text-rose-400 font-bold">•</span>
                        <span>{r}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500">No elevated risk factors detected.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column: Interactive Shipment Map */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Navigation className="w-3.5 h-3.5 text-blue-400" />
                  <span>Live Geospatial Tracking Map</span>
                </h4>
                <span className="text-[10px] text-slate-500 font-mono">Real-Time Leaflet</span>
              </div>
              <ShipmentMap
                origin={mapData?.origin}
                destination={mapData?.destination}
                currentLocation={mapData?.current_location}
                activeRoutePoints={mapData?.active_route?.points || []}
                disruptions={mapData?.disruptions || []}
                fleetAssets={mapData?.fleet_assets || []}
                coldChainEnabled={shipment.cold_chain_enabled}
                currentTemperature={coldChainData?.current_temperature}
                isColdChainCritical={coldChainData?.has_active_excursion}
                height="340px"
              />
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Cold Chain IoT Telemetry */}
      {activeTab === 'coldchain' && (
        <div className="space-y-5">
          {!shipment.cold_chain_enabled ? (
            <div className="p-8 text-center text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
              <ThermometerSnowflake className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p className="text-sm font-semibold text-slate-300">Cold Chain Inactive</p>
              <p className="text-xs">This consignment is classified as non-temperature sensitive dry cargo.</p>
            </div>
          ) : (
            <>
              {/* Cold Chain Status Summary */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Current Temp</span>
                  <div className={`mt-1 text-2xl font-bold font-mono ${
                    coldChainData?.has_active_excursion ? 'text-rose-400 animate-pulse' : 'text-cyan-400'
                  }`}>
                    {coldChainData?.current_temperature !== undefined && coldChainData?.current_temperature !== null
                      ? `${coldChainData.current_temperature.toFixed(1)}°C`
                      : 'N/A'}
                  </div>
                </div>

                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Allowed Range</span>
                  <div className="mt-1 text-sm font-bold font-mono text-slate-200">
                    {shipment.minimum_temperature}°C – {shipment.maximum_temperature}°C
                  </div>
                  <span className="text-[10px] text-slate-500">{coldChainData?.compliance_profile_name}</span>
                </div>

                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Peak Excursion</span>
                  <div className="mt-1 text-sm font-bold font-mono text-rose-300">
                    {coldChainData?.peak_temperature ? `${coldChainData.peak_temperature}°C` : 'None'}
                  </div>
                  <span className="text-[10px] text-slate-500">Duration: {coldChainData?.duration_minutes || 0} mins</span>
                </div>

                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Excursion Severity</span>
                  <div className="mt-1">
                    <StatusBadge status={coldChainData?.excursion_severity || 'NORMAL'} />
                  </div>
                </div>
              </div>

              {/* Predictive Warning Banner */}
              {coldChainData?.predictive_analysis?.status === 'BREACH_LIKELY' && (
                <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-800/80 flex items-center gap-3 text-amber-300 text-xs">
                  <AlertCircle className="w-5 h-5 shrink-0 text-amber-400 animate-bounce" />
                  <div>
                    <span className="font-bold uppercase tracking-wide">Predictive Alert: </span>
                    <span>{coldChainData.predictive_analysis.message}</span>
                  </div>
                </div>
              )}

              {/* Active Critical Excursion Warning Banner */}
              {coldChainData?.has_active_excursion && (
                <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-700/80 text-rose-200 space-y-1">
                  <div className="flex items-center gap-2 text-rose-300 font-bold text-xs uppercase tracking-wider">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    <span>CRITICAL COLD-CHAIN EXCURSION DETECTED</span>
                  </div>
                  <p className="text-xs">
                    Current reading ({coldChainData.current_temperature}°C) breaches the permissible upper limit of {shipment.maximum_temperature}°C. 
                    Recommended Action: Immediate quality quarantine protocol upon berth arrival.
                  </p>
                </div>
              )}

              {/* IoT Telemetry Simulator Controls */}
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">IoT Sensor Simulator</h4>
                    <p className="text-[11px] text-slate-400">Inject calibrated temperature readings into the live control tower pipeline</p>
                  </div>
                  <button
                    onClick={() => setIsLiveSimulating(!isLiveSimulating)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                      isLiveSimulating
                        ? 'bg-rose-600 hover:bg-rose-500 text-white animate-pulse'
                        : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                    }`}
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>{isLiveSimulating ? 'Stop Live Feed' : 'Start Live Simulation'}</span>
                  </button>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    onClick={() => handleSimulate('normal')}
                    className="px-3 py-1.5 rounded-lg bg-emerald-950/70 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-xs font-semibold transition-colors"
                  >
                    Simulate Normal (4.5°C)
                  </button>
                  <button
                    onClick={() => handleSimulate('warning')}
                    className="px-3 py-1.5 rounded-lg bg-amber-950/70 hover:bg-amber-900 border border-amber-800 text-amber-300 text-xs font-semibold transition-colors"
                  >
                    Simulate Warning (8.2°C)
                  </button>
                  <button
                    onClick={() => handleSimulate('critical')}
                    className="px-3 py-1.5 rounded-lg bg-rose-950/80 hover:bg-rose-900 border border-rose-700 text-rose-300 text-xs font-bold transition-colors"
                  >
                    Simulate Critical Excursion (10.2°C)
                  </button>
                </div>
              </div>

              {/* Telemetry Log */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Recent Sensor Telemetry Log</h4>
                <div className="max-h-48 overflow-y-auto border border-slate-800 rounded-lg">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900 text-slate-400 sticky top-0">
                      <tr>
                        <th className="p-2">Timestamp</th>
                        <th className="p-2">Temperature</th>
                        <th className="p-2">Humidity</th>
                        <th className="p-2">Excursion</th>
                        <th className="p-2">Severity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 bg-[#0d1424]">
                      {coldChainData?.recent_readings?.slice(-8).reverse().map((r: SensorReading) => (
                        <tr key={r.id}>
                          <td className="p-2 text-slate-400">{new Date(r.timestamp).toLocaleTimeString()}</td>
                          <td className={`p-2 font-bold ${r.is_excursion ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {r.temperature.toFixed(1)}°C
                          </td>
                          <td className="p-2 text-slate-300">{r.humidity?.toFixed(0)}%</td>
                          <td className="p-2">{r.is_excursion ? 'YES' : 'NO'}</td>
                          <td className="p-2">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              r.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-300' : r.severity === 'MAJOR' ? 'bg-orange-950 text-orange-300' : r.severity === 'WARNING' ? 'bg-amber-950 text-amber-300' : 'bg-emerald-950 text-emerald-300'
                            }`}>
                              {r.severity}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Tab 3: Route Alternatives (What-If Analysis & Map Simulator) */}
      {activeTab === 'routes' && (
        <div className="space-y-5">
          {/* Header & Description */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-blue-400" />
                <span>What-If Corridor Optimisation & Interactive Map</span>
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Evaluate autonomous rerouting corridors against active maritime disruptions. Select an alternative to preview on map.
              </p>
            </div>
            {selectedPreviewRoute && (
              <button
                onClick={() => setSelectedPreviewRoute(null)}
                className="px-2.5 py-1 text-[11px] font-semibold text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 rounded border border-slate-700 transition-colors flex items-center gap-1.5 self-start sm:self-auto"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Map to Active Corridor</span>
              </button>
            )}
          </div>

          {/* Interactive Map */}
          <div className="space-y-2">
            <ShipmentMap
              origin={mapData?.origin}
              destination={mapData?.destination}
              currentLocation={mapData?.current_location}
              activeRoutePoints={mapData?.active_route?.points || []}
              previewRoutePoints={selectedPreviewRoute?.stops || []}
              previewRouteName={selectedPreviewRoute?.name}
              disruptions={mapData?.disruptions || []}
              fleetAssets={mapData?.fleet_assets || []}
              coldChainEnabled={shipment.cold_chain_enabled}
              currentTemperature={coldChainData?.current_temperature}
              isColdChainCritical={coldChainData?.has_active_excursion}
              height="360px"
            />
          </div>

          {/* Route Comparison Selector Strip */}
          <div className="space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Select Corridor To Compare:</span>
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <button
                onClick={() => setSelectedPreviewRoute(null)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                  !selectedPreviewRoute
                    ? 'bg-blue-600 text-white shadow-sm ring-1 ring-blue-400'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span>● Active Corridor</span>
              </button>
              {routeAlternatives.map((alt, idx) => {
                const isSelected = selectedPreviewRoute?.id === alt.id;
                const isApproved = isRouteApproved(alt);
                return (
                  <button
                    key={alt.id || idx}
                    onClick={() => setSelectedPreviewRoute(isSelected ? null : alt)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-sm'
                        : isApproved
                        ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/60'
                        : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                    }`}
                  >
                    {isApproved ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-amber-400 animate-pulse' : 'bg-slate-600'}`} />
                    )}
                    <span>{alt.name}</span>
                    {alt.projected_risk_score !== undefined && (
                      <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                        {alt.projected_risk_score} risk
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Preview Banner (if previewing) */}
          {selectedPreviewRoute && (
            <div className="p-3 rounded-xl bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Previewing Detour:</span>
                  <span className="text-xs font-bold text-white">{selectedPreviewRoute.name}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span>Transit Delta: <strong className="text-slate-200 font-mono">+{selectedPreviewRoute.additional_time_hours}h</strong></span>
                  <span>•</span>
                  <span>Cost Delta: <strong className="text-slate-200 font-mono">+${selectedPreviewRoute.additional_cost_usd?.toLocaleString()}</strong></span>
                  <span>•</span>
                  <span>Projected Risk: <strong className="text-emerald-400 font-mono">{selectedPreviewRoute.projected_risk_score}/100</strong></span>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => setSelectedPreviewRoute(null)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/80 transition-colors"
                >
                  Clear Preview
                </button>
                <button
                  onClick={() => handleApproveRoute(selectedPreviewRoute)}
                  disabled={isApproving || isRouteApproved(selectedPreviewRoute)}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all shadow-md flex items-center gap-1.5 ${
                    isRouteApproved(selectedPreviewRoute)
                      ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/60 cursor-default'
                      : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30'
                  }`}
                >
                  {isApproving ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Applying Reroute...</span>
                    </>
                  ) : isRouteApproved(selectedPreviewRoute) ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Currently Active Corridor</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Approve & Persist Reroute</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Alternative Route Detailed Cards */}
          <div className="space-y-3">
            {routeAlternatives.map((alt) => {
              const isSelected = selectedPreviewRoute?.id === alt.id;
              const isApproved = isRouteApproved(alt);

              return (
                <div
                  key={alt.id}
                  className={`p-4 rounded-xl bg-slate-900/80 border transition-all space-y-3 ${
                    isApproved
                      ? 'border-emerald-500/60 bg-emerald-950/10 ring-1 ring-emerald-500/30'
                      : isSelected
                      ? 'border-amber-500/60 bg-amber-950/10 ring-1 ring-amber-500/20'
                      : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-sm text-white">{alt.name}</span>
                        {alt.tag && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800">
                            {alt.tag}
                          </span>
                        )}
                        {isApproved && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-700 flex items-center gap-1 shadow-sm">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span>Approved Active Route</span>
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">{alt.summary}</p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => setSelectedPreviewRoute(isSelected ? null : alt)}
                        className={`px-3 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                          isSelected
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {isSelected ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        <span>{isSelected ? 'Hide Preview' : 'Preview on Map'}</span>
                      </button>

                      <button
                        onClick={() => handleApproveRoute(alt)}
                        disabled={isApproving || isApproved}
                        className={`px-4 py-2 rounded-lg text-xs font-bold transition-all shrink-0 shadow-md flex items-center gap-1.5 ${
                          isApproved
                            ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/60 cursor-default'
                            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/30'
                        }`}
                      >
                        {isApproving ? (
                          <>
                            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span>Saving...</span>
                          </>
                        ) : isApproved ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Active Corridor</span>
                          </>
                        ) : (
                          <span>Approve Reroute</span>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Waypoint Sequence Chips */}
                  {alt.waypoints && alt.waypoints.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/60">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 block mb-1.5">
                        Planned Waypoint Progression:
                      </span>
                      <div className="flex flex-wrap items-center gap-1.5">
                        {alt.waypoints.map((wp: string, idx: number) => (
                          <React.Fragment key={idx}>
                            <span className={`px-2 py-0.5 rounded text-[11px] font-mono ${
                              idx === 0
                                ? 'bg-blue-950 text-blue-300 border border-blue-800'
                                : idx === alt.waypoints.length - 1
                                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                                : 'bg-slate-800/80 text-slate-300 border border-slate-700'
                            }`}>
                              {wp}
                            </span>
                            {idx < alt.waypoints.length - 1 && (
                              <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-xs">
                    <div>
                      <span className="text-slate-500 block text-[10px]">Transit Delta:</span>
                      <span className="font-semibold text-slate-200 font-mono">+{alt.additional_time_hours}h</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Freight Delta:</span>
                      <span className="font-semibold text-slate-200 font-mono">+${alt.additional_cost_usd?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Projected Risk:</span>
                      <span className="font-semibold text-emerald-400 font-mono">{alt.projected_risk_score} / 100</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Cold-Chain:</span>
                      <span className={`font-semibold ${alt.cold_chain_compatible ? 'text-cyan-300' : 'text-amber-400'}`}>
                        {alt.cold_chain_compatible ? 'Verified Compatible' : 'Uncertified'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 4: Carrier Ranking */}
      {activeTab === 'carriers' && (
        <div className="space-y-4">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">Alternative Carrier Evaluation</h4>
            <p className="text-[11px] text-slate-400">Ranked by schedule reliability, cost index, and cold-chain compliance</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {carrierAlternatives.map((c) => (
              <div key={c.carrier_id} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-slate-100">{c.carrier_name}</span>
                  {c.tag && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                      {c.tag}
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs pt-1">
                  <div>
                    <span className="text-[10px] text-slate-500 block">Reliability</span>
                    <span className="font-mono font-semibold text-emerald-400">{c.reliability_score}%</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">Transit Mult.</span>
                    <span className="font-mono font-semibold text-slate-300">{c.transit_multiplier}x</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">Est. Cost</span>
                    <span className="font-mono font-semibold text-slate-300">${c.estimated_cost_usd.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 5: Fleet Matching */}
      {activeTab === 'fleet' && (
        <div className="space-y-4">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">Compatible Physical Logistics Assets</h4>
            <p className="text-[11px] text-slate-400">Matched by cargo refrigeration requirements, payload capacity, and positioning proximity</p>
          </div>

          <div className="space-y-2">
            {fleetMatches.map((f) => (
              <div key={f.asset_id} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-100">{f.asset_identifier}</span>
                    <span className="text-slate-400">({f.asset_type} • {f.capacity} {f.capacity_unit})</span>
                    <StatusBadge status={f.status} />
                    {f.is_refrigerated && (
                      <span className="text-[10px] text-cyan-300 bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800">
                        Reefer
                      </span>
                    )}
                  </div>
                  <p className="text-slate-400 text-[11px]">Position: {f.current_location} • Suitability Score: {f.suitability_score}/100</p>
                </div>

                <span className={`px-2.5 py-1 rounded text-[11px] font-bold ${
                  f.is_compatible ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'
                }`}>
                  {f.is_compatible ? 'Compatible' : 'Incompatible'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 6: Bob / AI Assistant Decision Support */}
      {activeTab === 'ai' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-100">
                  {aiDecision?.provider_label || 'Bob Decision Support Assistant'}
                </h4>
                <p className="text-[11px] text-slate-400">Root-cause supply chain synthesis and structured operational advice</p>
              </div>
            </div>

            <button
              onClick={handleFetchAi}
              disabled={isAiLoading}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-colors flex items-center gap-1"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isAiLoading ? 'animate-spin' : ''}`} />
              <span>{isAiLoading ? 'Synthesizing...' : 'Regenerate Analysis'}</span>
            </button>
          </div>

          {aiDecision?.disclaimer && (
            <div className="p-3 bg-amber-950/30 border border-amber-800/60 rounded-lg text-amber-300 text-xs">
              {aiDecision.disclaimer}
            </div>
          )}

          {isAiLoading ? (
            <div className="p-8 text-center text-slate-400">Synthesizing disruption impact and telemetry...</div>
          ) : aiDecision ? (
            <div className="p-5 rounded-xl bg-slate-900/90 border border-indigo-900/40 space-y-4 text-xs">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Situation Overview</span>
                <p className="text-slate-200 leading-relaxed font-medium">{aiDecision.situation_summary}</p>
              </div>

              <div className="p-3 bg-indigo-950/40 border border-indigo-800/60 rounded-lg">
                <span className="text-[10px] uppercase font-bold text-indigo-300 block mb-1">Recommended Action</span>
                <p className="text-indigo-100 font-bold">{aiDecision.recommended_action}</p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Operational Rationale</span>
                <p className="text-slate-300 leading-relaxed">{aiDecision.rationale}</p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Tradeoff Analysis</span>
                <ul className="space-y-1">
                  {aiDecision.tradeoffs.map((t, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-slate-300">
                      <span className="text-blue-400 font-bold">•</span>
                      <span>{t}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 border-t border-slate-800 text-xs">
                <div>
                  <span className="text-slate-500 block text-[10px]">Risk Mitigation</span>
                  <span className="font-bold text-emerald-400 font-mono">
                    {aiDecision.risk_impact.from_risk} → {aiDecision.risk_impact.to_risk}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">Schedule Impact</span>
                  <span className="font-bold text-slate-300 font-mono">{aiDecision.time_impact}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">Cost Impact</span>
                  <span className="font-bold text-slate-300 font-mono">{aiDecision.cost_impact}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">Confidence</span>
                  <span className="font-bold text-indigo-400 font-mono">{(aiDecision.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </Modal>
  );
};
