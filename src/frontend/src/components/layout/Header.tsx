import React, { useState } from 'react';
import { Play, Sparkles, RefreshCw, CheckCircle2, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';

interface HeaderProps {
  currentTab: string;
  onRefreshData: () => void;
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onRefreshData, onShowToast }) => {
  const [isRunningDemo, setIsRunningDemo] = useState(false);

  const tabTitles: Record<string, { title: string; desc: string }> = {
    dashboard: { title: 'Control Tower Dashboard', desc: 'Real-time supply chain disruption monitoring & fleet intelligence' },
    copilot: { title: 'IBM Bob Copilot', desc: 'Conversational L2 Supply Chain Decision Support & MCP Tools' },
    shipments: { title: 'Shipment Operations', desc: 'Active cargo tracking, deterministic risk scoring, and route alternatives' },
    disruptions: { title: 'Disruption Management', desc: 'Geographic and maritime event tracking with automated impact analysis' },
    alerts: { title: 'Operational Alerts', desc: 'Prioritized event feed with 1-click decision approval' },
    fleet: { title: 'Fleet Utilisation & Assets', desc: 'Asset tracking, idle detection, and intelligent repositioning recommendations' },
  };

  const handleRunHackathonDemo = async () => {
    setIsRunningDemo(true);
    try {
      const res = await api.runHackathonDemo();
      onShowToast(
        `Demo scenario executed! SH-1024 Vaccines affected by Mumbai Port Strike (Risk: ${res.affected_shipment.final_excursion_risk}/100 CRITICAL).`,
        'success'
      );
      onRefreshData();
    } catch (err: any) {
      onShowToast(`Failed to run demo: ${err.message}`, 'error');
    } finally {
      setIsRunningDemo(false);
    }
  };

  const currentMeta = tabTitles[currentTab] || { title: 'RouteWise AI', desc: 'Supply Chain Control Tower' };

  return (
    <header className="h-16 px-6 bg-[#0c1220] border-b border-slate-800/80 flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-base font-bold text-white tracking-tight">{currentMeta.title}</h1>
        <p className="text-xs text-slate-400">{currentMeta.desc}</p>
      </div>

      <div className="flex items-center gap-3">
        {/* System Health Status Indicator */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Active Telematics Feed</span>
        </div>

        {/* Refresh Data */}
        <button
          onClick={onRefreshData}
          title="Refresh operational data"
          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg border border-slate-800 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Hero Hackathon Demo Runner Button */}
        <button
          onClick={handleRunHackathonDemo}
          disabled={isRunningDemo}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all shadow-md ${
            isRunningDemo
              ? 'bg-blue-800 text-slate-300 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-900/30'
          }`}
        >
          <Sparkles className={`w-4 h-4 ${isRunningDemo ? 'animate-spin text-blue-300' : 'text-amber-300'}`} />
          <span>{isRunningDemo ? 'Simulating Workflow...' : 'Run Hackathon Demo'}</span>
        </button>
      </div>
    </header>
  );
};
