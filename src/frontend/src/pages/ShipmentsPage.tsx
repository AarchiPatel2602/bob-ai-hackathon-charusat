import React, { useState, useEffect } from 'react';
import { Shipment } from '../types';
import { api } from '../services/api';
import { RiskBadge } from '../components/common/RiskBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { AddShipmentModal } from '../components/shipments/AddShipmentModal';
import { ShipmentDetailModal } from '../components/shipments/ShipmentDetailModal';
import { 
  Plus, 
  Search, 
  Filter, 
  ThermometerSnowflake, 
  ArrowRight, 
  Calendar, 
  Truck, 
  DollarSign,
  PackageCheck,
  RefreshCw
} from 'lucide-react';

interface ShipmentsPageProps {
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
  initialSelectedId?: number | null;
  onClearSelectedId?: () => void;
}

export const ShipmentsPage: React.FC<ShipmentsPageProps> = ({
  onShowToast,
  initialSelectedId,
  onClearSelectedId
}) => {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('ALL');
  
  // Modals
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [selectedShipmentId, setSelectedShipmentId] = useState<number | null>(null);

  useEffect(() => {
    if (initialSelectedId) {
      setSelectedShipmentId(initialSelectedId);
      if (onClearSelectedId) onClearSelectedId();
    }
  }, [initialSelectedId]);

  const fetchShipments = async () => {
    setIsLoading(true);
    try {
      let filterParams: any = { search: searchTerm };
      if (selectedFilter === 'COLD_CHAIN') {
        filterParams.cold_chain_only = true;
      } else if (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(selectedFilter)) {
        filterParams.risk_level = selectedFilter;
      } else if (selectedFilter !== 'ALL') {
        filterParams.status = selectedFilter;
      }

      const res = await api.getShipments(filterParams);
      setShipments(res);
    } catch (err: any) {
      onShowToast(`Failed to load shipments: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchShipments();
  }, [selectedFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchShipments();
  };

  const filters = [
    { id: 'ALL', label: 'All' },
    { id: 'PLANNED', label: 'Planned' },
    { id: 'IN_TRANSIT', label: 'In Transit' },
    { id: 'DELAYED', label: 'Delayed' },
    { id: 'DELIVERED', label: 'Delivered' },
    { id: 'AT_RISK', label: 'At Risk' },
    { id: 'CRITICAL', label: 'Critical' },
    { id: 'COLD_CHAIN', label: 'Cold Chain' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <PackageCheck className="w-5 h-5 text-blue-400" />
            <span>Active Shipments Registry</span>
          </h2>
          <p className="text-xs text-slate-400">Manage real-time manifests, autonomous risk tracking, and routing directives</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsAddOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg shadow-md shadow-blue-900/30 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>+ Add Shipment</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Strip */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#111827] p-3 rounded-xl border border-slate-800">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search by ID, Origin, Destination, Cargo, or Carrier..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700/80 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </form>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
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
      </div>

      {/* Shipment Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400">Loading shipments...</div>
      ) : shipments.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-[#111827] rounded-xl border border-slate-800 space-y-3">
          <PackageCheck className="w-10 h-10 mx-auto text-slate-600" />
          <p className="text-sm font-semibold text-slate-200">No shipments found</p>
          <p className="text-xs text-slate-500">Your supply chain is not configured yet or matches no filter parameters.</p>
          <button
            onClick={() => setIsAddOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-500"
          >
            + Add First Shipment
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shipments.map((s) => (
            <div
              key={s.id}
              className="p-4 rounded-xl bg-[#111827] border border-slate-800 hover:border-slate-700 hover:bg-slate-900/50 transition-all flex flex-col justify-between group relative overflow-hidden"
            >
              {/* Top Row: ID, Badges */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sm text-white group-hover:text-blue-400 transition-colors">
                    {s.shipment_identifier}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <StatusBadge status={s.status} />
                    <RiskBadge score={s.risk_score} level={s.risk_level} />
                  </div>
                </div>

                {/* Corridor */}
                <div className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <span>{s.origin}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>{s.destination}</span>
                </div>

                {/* Cargo & Value */}
                <div className="flex items-center justify-between text-xs py-1 border-y border-slate-800/60">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Cargo</span>
                    <span className="text-slate-200 font-medium">{s.cargo_type}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Value</span>
                    <span className="text-emerald-400 font-mono font-bold">${s.cargo_value.toLocaleString()}</span>
                  </div>
                </div>

                {/* Carrier & Cold Chain */}
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                  <div>
                    <span className="text-[10px] text-slate-500 block">Carrier:</span>
                    <span className="text-slate-300 font-medium truncate block">{s.carrier}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">Cold Chain:</span>
                    {s.cold_chain_enabled ? (
                      <span className="text-cyan-400 font-semibold inline-flex items-center gap-1">
                        <ThermometerSnowflake className="w-3 h-3" />
                        <span>{s.minimum_temperature}°C – {s.maximum_temperature}°C</span>
                      </span>
                    ) : (
                      <span className="text-slate-500">Dry Cargo</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Bottom Action */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[10px] text-slate-500 font-mono">
                  Location: <span className="text-slate-400">{s.current_location}</span>
                </span>
                <button
                  onClick={() => setSelectedShipmentId(s.id)}
                  className="px-3 py-1.5 rounded-lg bg-blue-600/15 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-semibold transition-colors flex items-center gap-1"
                >
                  <span>View Details</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Shipment Modal */}
      <AddShipmentModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onShipmentCreated={fetchShipments}
        onShowToast={onShowToast}
      />

      {/* Detail Modal */}
      <ShipmentDetailModal
        shipmentId={selectedShipmentId}
        isOpen={selectedShipmentId !== null}
        onClose={() => setSelectedShipmentId(null)}
        onUpdated={fetchShipments}
        onShowToast={onShowToast}
      />
    </div>
  );
};
