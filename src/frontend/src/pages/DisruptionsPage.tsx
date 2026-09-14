import React, { useState, useEffect } from 'react';
import { Disruption } from '../types';
import { api } from '../services/api';
import { ReportDisruptionModal } from '../components/disruptions/ReportDisruptionModal';
import { StatusBadge } from '../components/common/StatusBadge';
import { 
  AlertTriangle, 
  Radio, 
  MapPin, 
  Calendar, 
  DollarSign, 
  Package, 
  Plus, 
  CheckCircle2, 
  Activity, 
  Clock,
  ArrowRight
} from 'lucide-react';

interface DisruptionsPageProps {
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
  onSelectShipment: (id: number) => void;
}

export const DisruptionsPage: React.FC<DisruptionsPageProps> = ({
  onShowToast,
  onSelectShipment
}) => {
  const [disruptions, setDisruptions] = useState<Disruption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState('ALL');
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [selectedImpact, setSelectedImpact] = useState<any | null>(null);

  const fetchDisruptions = async () => {
    setIsLoading(true);
    try {
      let params: any = {};
      if (['ACTIVE', 'RESOLVED'].includes(selectedFilter)) {
        params.status = selectedFilter;
      } else if (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(selectedFilter)) {
        params.severity = selectedFilter;
      }
      const res = await api.getDisruptions(params);
      setDisruptions(res);
    } catch (err: any) {
      onShowToast(`Failed to load disruptions: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDisruptions();
  }, [selectedFilter]);

  const handleAnalyze = async (d: Disruption) => {
    try {
      const res = await api.analyzeDisruption(d.id);
      setSelectedImpact(res);
      onShowToast(`Impact analysis for ${d.name} refreshed.`, 'info');
      fetchDisruptions();
    } catch (err: any) {
      onShowToast(`Error analyzing impact: ${err.message}`, 'error');
    }
  };

  const filters = [
    { id: 'ALL', label: 'All' },
    { id: 'ACTIVE', label: 'Active' },
    { id: 'RESOLVED', label: 'Resolved' },
    { id: 'CRITICAL', label: 'Critical' },
    { id: 'HIGH', label: 'High' },
    { id: 'MEDIUM', label: 'Medium' },
    { id: 'LOW', label: 'Low' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <Radio className="w-5 h-5 text-purple-400" />
            <span>Supply Chain Disruption Registry</span>
          </h2>
          <p className="text-xs text-slate-400">Continuous spatial correlation of extreme weather, port strikes, and route bottlenecks</p>
        </div>

        <button
          onClick={() => setIsReportOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-lg shadow-md shadow-rose-900/30 transition-colors self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>+ Report Disruption</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-1.5 bg-[#111827] p-2 rounded-xl border border-slate-800 overflow-x-auto">
        {filters.map((f) => {
          const active = selectedFilter === f.id;
          return (
            <button
              key={f.id}
              onClick={() => setSelectedFilter(f.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                active
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      {/* Disruption Cards */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400">Loading disruptions...</div>
      ) : disruptions.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-[#111827] rounded-xl border border-slate-800 space-y-3">
          <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-500" />
          <p className="text-sm font-semibold text-slate-200">No active disruptions reported</p>
          <p className="text-xs text-slate-500">All corridors and maritime terminals are operating under nominal schedules.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {disruptions.map((d) => (
            <div
              key={d.id}
              className="p-5 rounded-xl bg-[#111827] border border-slate-800 hover:border-slate-700/80 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-white leading-tight">{d.name}</h3>
                    <p className="text-xs text-slate-400 flex items-center gap-1 mt-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      <span>{d.location}</span>
                    </p>
                  </div>
                  <StatusBadge status={d.severity} />
                </div>

                {d.description && (
                  <p className="text-xs text-slate-300 line-clamp-2">{d.description}</p>
                )}

                <div className="grid grid-cols-2 gap-2 text-xs bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold">Type</span>
                    <span className="text-slate-200 font-medium">{d.type}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold">Est. Duration</span>
                    <span className="text-slate-200 font-mono font-semibold">{d.expected_duration_days} days</span>
                  </div>
                </div>

                {/* Impact stats */}
                <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-900/40 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-[10px] text-rose-300 uppercase block font-bold">Affected Cargo</span>
                    <span className="text-rose-200 font-mono font-bold text-sm">
                      {d.affected_shipments_count} Shipments
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-rose-300 uppercase block font-bold">Value Exposed</span>
                    <span className="text-rose-200 font-mono font-bold text-sm">
                      ${(d.cargo_value_at_risk).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action */}
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                <StatusBadge status={d.status} />
                <button
                  onClick={() => handleAnalyze(d)}
                  className="px-3 py-1.5 bg-blue-600/15 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1"
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>Impact Analysis</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Impact Analysis Drawer / Modal */}
      {selectedImpact && (
        <div className="p-5 bg-slate-900 border border-blue-500/40 rounded-xl space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Radio className="w-4 h-4 text-blue-400" />
                <span>Impact Assessment: {selectedImpact.disruption_name}</span>
              </h3>
              <p className="text-xs text-slate-400">
                {selectedImpact.affected_shipments_count} active shipments identified • Total cargo value at risk: ${selectedImpact.cargo_value_at_risk.toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => setSelectedImpact(null)}
              className="text-xs text-slate-400 hover:text-white px-2 py-1 bg-slate-800 rounded"
            >
              Dismiss
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="p-2 bg-slate-950 rounded border border-rose-900/50">
              <span className="text-[10px] text-rose-400 uppercase font-semibold">Critical Shipments</span>
              <p className="text-base font-bold text-rose-300 font-mono">{selectedImpact.critical_count}</p>
            </div>
            <div className="p-2 bg-slate-950 rounded border border-orange-900/50">
              <span className="text-[10px] text-orange-400 uppercase font-semibold">High Risk</span>
              <p className="text-base font-bold text-orange-300 font-mono">{selectedImpact.high_count}</p>
            </div>
            <div className="p-2 bg-slate-950 rounded border border-cyan-900/50">
              <span className="text-[10px] text-cyan-400 uppercase font-semibold">Cold Chain At Risk</span>
              <p className="text-base font-bold text-cyan-300 font-mono">{selectedImpact.cold_chain_count}</p>
            </div>
            <div className="p-2 bg-slate-950 rounded border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Medium / Low</span>
              <p className="text-base font-bold text-slate-300 font-mono">{selectedImpact.medium_count + selectedImpact.low_count}</p>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-300 block">Affected Shipments Roster:</span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-60 overflow-y-auto">
              {selectedImpact.affected_shipments.map((s: any) => (
                <div
                  key={s.id}
                  onClick={() => onSelectShipment(s.id)}
                  className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-blue-500/50 cursor-pointer transition-all flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-mono font-bold text-slate-100">{s.identifier}</span>
                    <p className="text-slate-400 text-[11px]">{s.origin} → {s.destination} ({s.cargo_type})</p>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-rose-400">{s.risk_score}/100</span>
                    <p className="text-[10px] text-slate-500">${(s.cargo_value).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Report Modal */}
      <ReportDisruptionModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        onDisruptionReported={fetchDisruptions}
        onShowToast={onShowToast}
      />
    </div>
  );
};
