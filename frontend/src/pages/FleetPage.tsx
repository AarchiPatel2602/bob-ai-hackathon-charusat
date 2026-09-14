import React, { useState, useEffect } from 'react';
import { FleetAsset, FleetUtilisation, FleetRedeploymentRecommendation } from '../types';
import { api } from '../services/api';
import { AddFleetModal } from '../components/fleet/AddFleetModal';
import { StatusBadge } from '../components/common/StatusBadge';
import { 
  Truck, 
  Plus, 
  ThermometerSnowflake, 
  ArrowRight, 
  TrendingUp, 
  Clock, 
  MapPin, 
  ShieldCheck,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

interface FleetPageProps {
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const FleetPage: React.FC<FleetPageProps> = ({ onShowToast }) => {
  const [assets, setAssets] = useState<FleetAsset[]>([]);
  const [utilisation, setUtilisation] = useState<FleetUtilisation | null>(null);
  const [recommendations, setRecommendations] = useState<FleetRedeploymentRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  const fetchFleetData = async () => {
    setIsLoading(true);
    try {
      const [fAssets, fUtil, fRecs] = await Promise.all([
        api.getFleet({ status: selectedStatus !== 'ALL' ? selectedStatus : undefined }),
        api.getFleetUtilisation(),
        api.getFleetRecommendations()
      ]);
      setAssets(fAssets);
      setUtilisation(fUtil);
      setRecommendations(fRecs);
    } catch (err: any) {
      onShowToast(`Failed to load fleet data: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFleetData();
  }, [selectedStatus]);

  const handleApproveRedeploy = async (rec: FleetRedeploymentRecommendation) => {
    try {
      await api.approveFleetRedeployment(rec.asset_id, rec.to_location);
      onShowToast(
        `Redeployment approved! ${rec.asset_identifier} dispatched from ${rec.from_location} to ${rec.to_location}. Utilisation improved.`,
        'success'
      );
      fetchFleetData();
    } catch (err: any) {
      onShowToast(`Failed to approve redeployment: ${err.message}`, 'error');
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <Truck className="w-5 h-5 text-cyan-400" />
            <span>Physical Fleet Management & Optimisation</span>
          </h2>
          <p className="text-xs text-slate-400">Autonomous idle asset detection, surge capacity re-allocation, and utilisation tracking</p>
        </div>

        <button
          onClick={() => setIsAddOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg shadow-md shadow-blue-900/30 transition-colors self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>+ Add Asset</span>
        </button>
      </div>

      {/* Utilisation Analytics Strip */}
      {utilisation && (
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Network Capacity Utilisation
              </h3>
            </div>
            <div className="text-xs text-slate-400 font-mono">
              Total Pool: <span className="font-bold text-white">{utilisation.total_capacity_tons} tons</span> across {utilisation.total_assets} units
            </div>
          </div>

          {/* Progress Bar showing current vs projected */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-300 font-semibold">
                Current Active Utilisation: <span className="text-cyan-400 font-mono font-bold">{utilisation.current_utilisation_pct}%</span>
              </span>
              {utilisation.improvement_pct > 0 && (
                <span className="text-emerald-400 font-semibold text-[11px] flex items-center gap-1">
                  <span>Target with Redeployment: {utilisation.projected_utilisation_pct}%</span>
                  <span className="px-1.5 py-0.2 bg-emerald-950 border border-emerald-800 rounded font-mono font-bold">
                    +{utilisation.improvement_pct}%
                  </span>
                </span>
              )}
            </div>

            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex">
              <div
                className="h-full bg-cyan-500 transition-all duration-500"
                style={{ width: `${utilisation.current_utilisation_pct}%` }}
              />
              {utilisation.improvement_pct > 0 && (
                <div
                  className="h-full bg-emerald-500/40 border-l border-emerald-400 transition-all duration-500"
                  style={{ width: `${utilisation.improvement_pct}%` }}
                />
              )}
            </div>
          </div>

          {/* Asset State Counts */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs">
            <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Available</span>
              <p className="text-base font-bold text-emerald-400 font-mono">{utilisation.available_assets}</p>
            </div>
            <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">In Transit</span>
              <p className="text-base font-bold text-blue-400 font-mono">{utilisation.in_transit_assets}</p>
            </div>
            <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Idle Assets</span>
              <p className="text-base font-bold text-amber-400 font-mono">{utilisation.idle_assets}</p>
            </div>
            <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Maintenance</span>
              <p className="text-base font-bold text-purple-400 font-mono">{utilisation.maintenance_assets}</p>
            </div>
          </div>
        </div>
      )}

      {/* Autonomous Redeployment Recommendations Panel */}
      {recommendations.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Autonomous Redeployment Recommendations ({recommendations.length})
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recommendations.map((rec) => (
              <div
                key={rec.asset_id}
                className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/60 flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-white">{rec.asset_identifier}</span>
                      <span className="text-xs text-slate-400">({rec.capacity} {rec.capacity_unit})</span>
                      {rec.is_refrigerated && (
                        <span className="text-[10px] text-cyan-300 bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800">
                          Reefer
                        </span>
                      )}
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
                      IDLE ASSET
                    </span>
                  </div>

                  <div className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                    <span>{rec.from_location}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span className="text-amber-300">{rec.to_location} (High Demand Hub)</span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{rec.reason}</p>
                </div>

                <div className="pt-2 border-t border-amber-900/40 flex items-center justify-between">
                  <span className="text-[11px] text-emerald-400 font-semibold font-mono">
                    Utilisation Impact: {rec.current_utilisation_pct}% → {rec.projected_utilisation_pct}%
                  </span>
                  <button
                    onClick={() => handleApproveRedeploy(rec)}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-colors shadow-sm shadow-emerald-900/40"
                  >
                    Approve Redeployment
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fleet Inventory Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Physical Fleet Inventory ({assets.length})
          </h3>

          <div className="flex items-center gap-1.5 text-xs">
            {['ALL', 'AVAILABLE', 'IN_TRANSIT', 'IDLE', 'MAINTENANCE'].map((st) => (
              <button
                key={st}
                onClick={() => setSelectedStatus(st)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  selectedStatus === st
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111827]">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="p-3">Asset ID</th>
                <th className="p-3">Type</th>
                <th className="p-3">Location</th>
                <th className="p-3">Capacity</th>
                <th className="p-3">Cold-Chain</th>
                <th className="p-3">Status</th>
                <th className="p-3">Current Assignment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {assets.map((a) => (
                <tr key={a.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-3 font-mono font-bold text-white">{a.asset_identifier}</td>
                  <td className="p-3 text-slate-300">{a.asset_type}</td>
                  <td className="p-3 text-slate-300 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-500" />
                    <span>{a.current_location}</span>
                  </td>
                  <td className="p-3 font-mono text-slate-200">{a.capacity} {a.capacity_unit}</td>
                  <td className="p-3">
                    {a.is_refrigerated ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800">
                        <ThermometerSnowflake className="w-3 h-3 text-cyan-400" />
                        <span>Reefer</span>
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[11px]">Dry Unit</span>
                    )}
                  </td>
                  <td className="p-3">
                    <StatusBadge status={a.status} />
                  </td>
                  <td className="p-3 text-slate-400 font-mono text-[11px]">
                    {a.current_assignment || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Asset Modal */}
      <AddFleetModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onAssetAdded={fetchFleetData}
        onShowToast={onShowToast}
      />
    </div>
  );
};
