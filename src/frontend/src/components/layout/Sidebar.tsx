import React from 'react';
import { 
  LayoutDashboard, 
  PackageCheck, 
  AlertTriangle, 
  Bell, 
  Truck, 
  ShieldAlert,
  LogOut,
  Sliders,
  UserCheck,
  Bot
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  unreadAlertCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, unreadAlertCount }) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'copilot', label: 'IBM Bob Copilot', icon: Bot },
    { id: 'shipments', label: 'Shipments', icon: PackageCheck },
    { id: 'disruptions', label: 'Disruptions', icon: AlertTriangle },
    { id: 'alerts', label: 'Alerts', icon: Bell, badge: unreadAlertCount },
    { id: 'fleet', label: 'Fleet', icon: Truck },
  ];

  return (
    <aside className="w-64 bg-[#0d1424] border-r border-slate-800 flex flex-col shrink-0 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 border-b border-slate-800/90 gap-3 bg-[#0a0f1c]">
        <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-400">
          <ShieldAlert className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-base tracking-tight text-white">RouteWise</span>
            <span className="px-1.5 py-0.2 bg-blue-600 text-white font-bold text-[10px] rounded uppercase tracking-wider">AI 🚢</span>
          </div>
          <p className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">Logistics Copilot</p>
        </div>
      </div>

      {/* Main Navigation Items */}
      <div className="flex-1 py-4 px-3 space-y-1">
        <p className="px-3 pb-2 text-[10px] uppercase font-bold text-slate-500 tracking-wider">Operations</p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* User and Bottom Section */}
      <div className="p-3 border-t border-slate-800/90 space-y-1 bg-[#090d17]">
        <div className="px-3 py-2 flex items-center gap-3 rounded-lg bg-slate-900/60 border border-slate-800/80 mb-2">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-blue-400 font-bold text-xs">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-200 truncate">{user?.full_name || 'Operator'}</p>
            <p className="text-[10px] text-slate-400 truncate">{user?.role || 'Logistics Manager'}</p>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2 text-xs font-medium text-slate-400 hover:text-rose-300 hover:bg-rose-950/30 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
