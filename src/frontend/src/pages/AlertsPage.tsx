import React, { useState, useEffect } from 'react';
import { Alert } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { 
  Bell, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ExternalLink, 
  CheckCheck,
  ShieldCheck,
  Filter
} from 'lucide-react';

interface AlertsPageProps {
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
  onSelectShipment: (id: number) => void;
  onAlertsChanged: () => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({
  onShowToast,
  onSelectShipment,
  onAlertsChanged
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState('ALL');

  const fetchAlerts = async () => {
    setIsLoading(true);
    try {
      let params: any = {};
      if (selectedFilter === 'UNREAD') {
        params.is_read = false;
      } else if (selectedFilter === 'RESOLVED') {
        params.is_resolved = true;
      } else if (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(selectedFilter)) {
        params.severity = selectedFilter;
      }

      const res = await api.getAlerts(params);
      setAlerts(res);
    } catch (err: any) {
      onShowToast(`Failed to load alerts: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [selectedFilter]);

  const handleMarkRead = async (id: number) => {
    try {
      await api.markAlertRead(id);
      fetchAlerts();
      onAlertsChanged();
    } catch (err: any) {
      onShowToast(`Error: ${err.message}`, 'error');
    }
  };

  const handleResolve = async (id: number) => {
    try {
      await api.resolveAlert(id);
      onShowToast('Alert marked as resolved.', 'info');
      fetchAlerts();
      onAlertsChanged();
    } catch (err: any) {
      onShowToast(`Error: ${err.message}`, 'error');
    }
  };

  const handleApproveAction = async (id: number) => {
    try {
      const res = await api.approveAlertAction(id);
      onShowToast('Reroute recommendation approved. Operational state recorded.', 'success');
      fetchAlerts();
      onAlertsChanged();
    } catch (err: any) {
      onShowToast(`Error: ${err.message}`, 'error');
    }
  };

  const filters = [
    { id: 'ALL', label: 'All' },
    { id: 'UNREAD', label: 'Unread' },
    { id: 'CRITICAL', label: 'Critical' },
    { id: 'HIGH', label: 'High' },
    { id: 'MEDIUM', label: 'Medium' },
    { id: 'LOW', label: 'Low' },
    { id: 'RESOLVED', label: 'Resolved' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <Bell className="w-5 h-5 text-blue-400" />
            <span>Autonomous Operational Alerts</span>
          </h2>
          <p className="text-xs text-slate-400">Continuous exception surveillance: Cold-chain excursions, delay risks, and reroute triggers</p>
        </div>
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
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      {/* Alerts Feed */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400">Loading alerts...</div>
      ) : alerts.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-[#111827] rounded-xl border border-slate-800 space-y-3">
          <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-500" />
          <p className="text-sm font-semibold text-slate-200">No active alerts matching criteria</p>
          <p className="text-xs text-slate-500">Your network operations are running without critical anomalies.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => {
            let borderStyle = 'border-slate-800';
            if (!a.is_read) borderStyle = 'border-blue-500/40 bg-blue-950/10';
            if (a.severity === 'CRITICAL' && !a.is_resolved) borderStyle = 'border-rose-700/60 bg-rose-950/20';

            return (
              <div
                key={a.id}
                className={`p-4 rounded-xl bg-[#111827] border ${borderStyle} transition-all space-y-3 relative overflow-hidden`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={a.severity} />
                    <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">{a.alert_type.replace('_', ' ')}</span>
                    {!a.is_read && (
                      <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-slate-500 text-xs font-mono">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(a.created_at).toLocaleTimeString()} • {new Date(a.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-white">{a.title}</h3>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">{a.reason}</p>
                </div>

                {a.recommended_action && (
                  <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300 flex items-start gap-2">
                    <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-blue-300">Recommended Action: </span>
                      <span>{a.recommended_action}</span>
                    </div>
                  </div>
                )}

                {/* Actions Strip */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/70 text-xs">
                  <div className="flex items-center gap-2">
                    {a.shipment_id && (
                      <button
                        onClick={() => onSelectShipment(a.shipment_id!)}
                        className="px-3 py-1 bg-blue-600/15 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 font-semibold rounded-lg transition-colors flex items-center gap-1"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>View Shipment</span>
                      </button>
                    )}
                    {!a.is_read && (
                      <button
                        onClick={() => handleMarkRead(a.id)}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
                      >
                        Mark Read
                      </button>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {!a.is_resolved ? (
                      <>
                        <button
                          onClick={() => handleApproveAction(a.id)}
                          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-colors shadow-sm shadow-emerald-900/30"
                        >
                          Approve Recommendation
                        </button>
                        <button
                          onClick={() => handleResolve(a.id)}
                          className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
                        >
                          Resolve
                        </button>
                      </>
                    ) : (
                      <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Resolved</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
