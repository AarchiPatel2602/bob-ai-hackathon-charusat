import React, { useState, useEffect } from 'react';
import { 
  Package, 
  AlertTriangle, 
  ShieldAlert, 
  DollarSign, 
  Truck, 
  ThermometerSnowflake, 
  Radio, 
  ArrowRight, 
  TrendingUp, 
  Activity, 
  CheckCircle2, 
  Clock, 
  Sparkles,
  Globe,
  RefreshCw
} from 'lucide-react';
import { DashboardSummary } from '../types';
import { RiskBadge } from '../components/common/RiskBadge';
import { api } from '../services/api';
import { ShipmentMap } from '../components/map/ShipmentMap';

interface DashboardPageProps {
  summary: DashboardSummary | null;
  isLoading: boolean;
  onNavigateTab: (tab: string) => void;
  onSelectShipment: (id: number) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  summary,
  isLoading,
  onNavigateTab,
  onSelectShipment
}) => {
  const [mapData, setMapData] = useState<{
    shipments: any[];
    disruptions: any[];
    fleet_assets: any[];
  } | null>(null);
  const [isMapLoading, setIsMapLoading] = useState(true);

  const fetchMapData = async () => {
    try {
      const data = await api.getDashboardMap();
      setMapData(data);
    } catch {
      // background error handled gracefully
    } finally {
      setIsMapLoading(false);
    }
  };

  useEffect(() => {
    fetchMapData();
    const interval = setInterval(fetchMapData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading || !summary) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <Activity className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-sm font-medium">Aggregating real-time supply chain telematics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* KPI Overview Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {/* Active Shipments */}
        <div 
          onClick={() => onNavigateTab('shipments')}
          className="bg-[#111827] p-4 rounded-xl border border-slate-800 hover:border-slate-700 cursor-pointer transition-all hover:bg-slate-900/60"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Active Cargo</span>
            <Package className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{summary.active_shipments}</div>
          <span className="text-[10px] text-slate-400">Total in transit</span>
        </div>

        {/* At Risk */}
        <div 
          onClick={() => onNavigateTab('shipments')}
          className="bg-[#111827] p-4 rounded-xl border border-amber-900/40 hover:border-amber-700/60 cursor-pointer transition-all hover:bg-amber-950/20"
        >
          <div className="flex items-center justify-between text-amber-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">At Risk</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 font-mono">{summary.at_risk_shipments}</div>
          <span className="text-[10px] text-amber-400/80">Risk Score &gt; 60</span>
        </div>

        {/* Critical */}
        <div 
          onClick={() => onNavigateTab('shipments')}
          className="bg-[#111827] p-4 rounded-xl border border-rose-900/50 hover:border-rose-700/80 cursor-pointer transition-all hover:bg-rose-950/30"
        >
          <div className="flex items-center justify-between text-rose-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Critical</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-300 font-mono">{summary.critical_shipments}</div>
          <span className="text-[10px] text-rose-400/80">Risk Score &gt; 80</span>
        </div>

        {/* Active Disruptions */}
        <div 
          onClick={() => onNavigateTab('disruptions')}
          className="bg-[#111827] p-4 rounded-xl border border-slate-800 hover:border-slate-700 cursor-pointer transition-all hover:bg-slate-900/60"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Disruptions</span>
            <Radio className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-300 font-mono">{summary.active_disruptions}</div>
          <span className="text-[10px] text-slate-400">Ports & Corridors</span>
        </div>

        {/* Cargo Value at Risk */}
        <div className="bg-[#111827] p-4 rounded-xl border border-rose-900/40 col-span-2 md:col-span-1 lg:col-span-1">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Value at Risk</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-300 font-mono truncate">
            ${(summary.cargo_value_at_risk / 1000).toFixed(0)}k
          </div>
          <span className="text-[10px] text-slate-400">Exposed assets</span>
        </div>

        {/* Fleet Utilisation */}
        <div 
          onClick={() => onNavigateTab('fleet')}
          className="bg-[#111827] p-4 rounded-xl border border-slate-800 hover:border-slate-700 cursor-pointer transition-all hover:bg-slate-900/60"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Fleet Util.</span>
            <Truck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-300 font-mono">{summary.fleet_utilisation_pct}%</div>
          <span className="text-[10px] text-slate-400">Active capacity</span>
        </div>

        {/* Cold Chain Alerts */}
        <div 
          onClick={() => onNavigateTab('alerts')}
          className="bg-[#111827] p-4 rounded-xl border border-cyan-900/40 hover:border-cyan-700/60 cursor-pointer transition-all hover:bg-cyan-950/20"
        >
          <div className="flex items-center justify-between text-cyan-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Cold Chain</span>
            <ThermometerSnowflake className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-300 font-mono">{summary.cold_chain_alerts_count}</div>
          <span className="text-[10px] text-cyan-400/80">Excursions / Warn</span>
        </div>
      </div>

      {/* Global Control Tower Live Geospatial Network Map */}
      <div className="bg-[#111827] rounded-xl border border-slate-800 p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Globe className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white tracking-wide">
                  Global Operational Control Tower — Live Network Map
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800">
                  REAL-TIME LEAFLET
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Visualizing active transit corridors, multimodal nodes, disruption alert zones, and mobile fleet positioning.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            {mapData && (
              <div className="hidden md:flex items-center gap-2 text-xs font-mono text-slate-400 mr-2">
                <span className="text-blue-400 font-bold">{mapData.shipments?.length || 0} Corridors</span>
                <span>•</span>
                <span className="text-purple-400 font-bold">{mapData.disruptions?.length || 0} Disruptions</span>
                <span>•</span>
                <span className="text-cyan-400 font-bold">{mapData.fleet_assets?.length || 0} Assets</span>
              </div>
            )}
            <button
              onClick={() => { setIsMapLoading(true); fetchMapData(); }}
              className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-400 hover:text-slate-200 border border-slate-700 transition-colors"
              title="Refresh Network Map"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isMapLoading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Map Canvas */}
        <div className="rounded-lg overflow-hidden border border-slate-800/80">
          <ShipmentMap
            shipmentsLayer={mapData?.shipments || []}
            disruptions={mapData?.disruptions || []}
            fleetAssets={mapData?.fleet_assets || []}
            onSelectShipment={onSelectShipment}
            height="440px"
            showControls={true}
            interactive={true}
          />
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-0.5 px-1">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-400" />
              <span>Normal Corridor</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span>Elevated Risk</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span>Critical Disruption</span>
            </span>
          </div>
          <span className="hidden sm:inline italic text-slate-400">
            Click any corridor line or node to inspect authoritative shipment details
          </span>
        </div>
      </div>

      {/* Main Content Grid: Critical Attention Panel & Live Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Critical Attention Panel (2 columns) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Critical Attention Required
              </h2>
            </div>
            <button
              onClick={() => onNavigateTab('shipments')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
            >
              <span>View all shipments</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {summary.critical_attention.length === 0 ? (
            <div className="p-8 rounded-xl bg-[#111827] border border-slate-800 text-center text-slate-400 space-y-2">
              <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-400" />
              <p className="text-sm font-semibold text-slate-200">All Corridors Operational</p>
              <p className="text-xs">No critical risk thresholds breached across active shipments.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {summary.critical_attention.map((item) => (
                <div
                  key={item.shipment_id}
                  onClick={() => onSelectShipment(item.shipment_id)}
                  className="p-4 rounded-xl bg-[#111827] border border-slate-800 hover:border-slate-700/80 hover:bg-slate-900/60 cursor-pointer transition-all group relative overflow-hidden"
                >
                  <div className={`absolute top-0 left-0 bottom-0 w-1 ${
                    item.risk_score >= 81 ? 'bg-rose-500' : 'bg-amber-500'
                  }`} />

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pl-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-sm text-white group-hover:text-blue-400 transition-colors">
                          {item.shipment_identifier}
                        </span>
                        <RiskBadge score={item.risk_score} level={item.risk_level} />
                        {item.has_cold_chain && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800">
                            <ThermometerSnowflake className="w-3 h-3 text-cyan-400" />
                            <span>{item.current_temp !== undefined && item.current_temp !== null ? `${item.current_temp.toFixed(1)}°C` : 'Cold Chain'}</span>
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-300 font-medium">
                        {item.origin_destination} • <span className="text-slate-400">{item.cargo_type}</span> (${(item.cargo_value).toLocaleString()})
                      </p>
                      <p className="text-xs text-slate-400">
                        <span className="text-slate-500 font-medium">Root Cause:</span> {item.reason}
                      </p>
                    </div>

                    <div className="flex items-center sm:self-center shrink-0">
                      <span className="text-xs text-blue-400 group-hover:text-blue-300 font-semibold flex items-center gap-1">
                        <span>Action Support</span>
                        <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Activity Feed (1 column) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Live Activity Feed
              </h2>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">AUTOMATIC</span>
          </div>

          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
            {summary.recent_activity.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">No recent events recorded</p>
            ) : (
              summary.recent_activity.map((act) => {
                let badgeColor = 'text-blue-400 bg-blue-950/60 border-blue-900';
                if (act.severity === 'CRITICAL') badgeColor = 'text-rose-400 bg-rose-950/60 border-rose-900';
                else if (act.severity === 'HIGH') badgeColor = 'text-orange-400 bg-orange-950/60 border-orange-900';
                else if (act.severity === 'MEDIUM') badgeColor = 'text-amber-400 bg-amber-950/60 border-amber-900';

                return (
                  <div key={act.id} className="flex gap-3 text-xs border-b border-slate-800/60 pb-3 last:border-0 last:pb-0">
                    <span className="font-mono text-slate-500 shrink-0 text-[11px] pt-0.5">
                      {act.time_str}
                    </span>
                    <div className="space-y-0.5 min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200 truncate">{act.title}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-2">{act.subtitle}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
