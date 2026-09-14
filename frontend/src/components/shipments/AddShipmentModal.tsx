import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../services/api';
import { Plus, Trash2, ThermometerSnowflake } from 'lucide-react';

interface AddShipmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShipmentCreated: () => void;
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const AddShipmentModal: React.FC<AddShipmentModalProps> = ({
  isOpen,
  onClose,
  onShipmentCreated,
  onShowToast
}) => {
  const [formData, setFormData] = useState({
    shipment_identifier: '',
    origin: '',
    destination: '',
    current_location: '',
    carrier: 'Maersk Line',
    cargo_type: 'Vaccines',
    cargo_description: '',
    cargo_value: 100000,
    priority: 'HIGH',
    status: 'IN_TRANSIT',
    cold_chain_enabled: false,
    minimum_temperature: 2.0,
    maximum_temperature: 8.0,
    required_fleet_type: 'Truck',
    required_capacity: 10.0,
    capacity_unit: 'tons'
  });

  const [routePoints, setRoutePoints] = useState<string[]>(['', '']);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const cargoTypes = [
    'Vaccines',
    'Pharmaceuticals',
    'Food',
    'Seafood',
    'Electronics',
    'Textiles',
    'Machinery',
    'Chemicals',
    'General Cargo'
  ];

  const carriers = [
    'Maersk Line',
    'MSC Mediterranean',
    'CMA CGM Group',
    'Hapag-Lloyd',
    'DHL Global Forwarding',
    'Kuehne + Nagel'
  ];

  const handleAddRoutePoint = () => {
    setRoutePoints([...routePoints, '']);
  };

  const handleRemoveRoutePoint = (index: number) => {
    setRoutePoints(routePoints.filter((_, i) => i !== index));
  };

  const handleRoutePointChange = (index: number, val: string) => {
    const updated = [...routePoints];
    updated[index] = val;
    setRoutePoints(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.shipment_identifier || !formData.origin || !formData.destination) {
      onShowToast('Please fill in required fields: ID, Origin, Destination.', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      const validPoints = routePoints.filter(p => p.trim() !== '').map((loc, idx) => ({
        location_name: loc,
        sequence_order: idx + 1,
        status: idx === 0 ? 'CURRENT' : 'PENDING'
      }));

      const payload = {
        ...formData,
        cargo_value: Number(formData.cargo_value),
        minimum_temperature: formData.cold_chain_enabled ? Number(formData.minimum_temperature) : null,
        maximum_temperature: formData.cold_chain_enabled ? Number(formData.maximum_temperature) : null,
        required_capacity: Number(formData.required_capacity),
        current_location: formData.current_location || formData.origin,
        route_points: validPoints.length > 0 ? validPoints : [
          { location_name: formData.origin, sequence_order: 1, status: 'CURRENT' },
          { location_name: formData.destination, sequence_order: 2, status: 'PENDING' }
        ]
      };

      await api.createShipment(payload);
      onShowToast(`Shipment ${formData.shipment_identifier} registered successfully. Risk score calculated.`, 'success');
      onShipmentCreated();
      onClose();
    } catch (err: any) {
      onShowToast(`Error creating shipment: ${err.message}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Register New Shipment" subtitle="Enter consignment manifests, telematics parameters, and routing waypoints" maxWidth="2xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Shipment Identifier *</label>
            <input
              type="text"
              placeholder="e.g. SH-1024"
              value={formData.shipment_identifier}
              onChange={(e) => setFormData({ ...formData, shipment_identifier: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Carrier</label>
            <select
              value={formData.carrier}
              onChange={(e) => setFormData({ ...formData, carrier: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {carriers.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Origin Node *</label>
            <input
              type="text"
              placeholder="e.g. Mumbai"
              value={formData.origin}
              onChange={(e) => setFormData({ ...formData, origin: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Destination Node *</label>
            <input
              type="text"
              placeholder="e.g. Rotterdam"
              value={formData.destination}
              onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Current Transit Location</label>
            <input
              type="text"
              placeholder="Defaults to origin if empty"
              value={formData.current_location}
              onChange={(e) => setFormData({ ...formData, current_location: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Cargo Type</label>
            <select
              value={formData.cargo_type}
              onChange={(e) => {
                const isCold = ['Vaccines', 'Pharmaceuticals', 'Food', 'Seafood'].includes(e.target.value);
                setFormData({
                  ...formData,
                  cargo_type: e.target.value,
                  cold_chain_enabled: isCold || formData.cold_chain_enabled
                });
              }}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {cargoTypes.map(ct => <option key={ct} value={ct}>{ct}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Declared Cargo Value (USD) *</label>
            <input
              type="number"
              value={formData.cargo_value}
              onChange={(e) => setFormData({ ...formData, cargo_value: Number(e.target.value) })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
              required
              min="0"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Priority</label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        </div>

        {/* Cold Chain Specifications */}
        <div className="p-4 rounded-lg bg-slate-900/80 border border-cyan-900/40 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ThermometerSnowflake className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">Cold-Chain Telematics</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.cold_chain_enabled}
                onChange={(e) => setFormData({ ...formData, cold_chain_enabled: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-600"></div>
              <span className="ml-2 text-xs font-medium text-slate-300">Enabled</span>
            </label>
          </div>

          {formData.cold_chain_enabled && (
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Min Temp (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.minimum_temperature}
                  onChange={(e) => setFormData({ ...formData, minimum_temperature: parseFloat(e.target.value) })}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded text-sm text-cyan-300 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Max Temp (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.maximum_temperature}
                  onChange={(e) => setFormData({ ...formData, maximum_temperature: parseFloat(e.target.value) })}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded text-sm text-cyan-300 font-mono"
                />
              </div>
            </div>
          )}
        </div>

        {/* Route Points */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300">Route Waypoints (e.g. Mumbai → Dubai → Rotterdam)</label>
            <button
              type="button"
              onClick={handleAddRoutePoint}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Waypoint</span>
            </button>
          </div>

          <div className="space-y-2">
            {routePoints.map((pt, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-500 w-5">{idx + 1}.</span>
                <input
                  type="text"
                  placeholder={`Waypoint ${idx + 1} location`}
                  value={pt}
                  onChange={(e) => handleRoutePointChange(idx, e.target.value)}
                  className="flex-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-white focus:outline-none focus:border-blue-500"
                />
                {routePoints.length > 2 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveRoutePoint(idx)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-colors shadow-lg shadow-blue-900/30"
          >
            {isSubmitting ? 'Registering...' : 'Save & Calculate Risk'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
