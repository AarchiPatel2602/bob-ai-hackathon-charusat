import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../services/api';
import { Truck, ThermometerSnowflake } from 'lucide-react';

interface AddFleetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAssetAdded: () => void;
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const AddFleetModal: React.FC<AddFleetModalProps> = ({
  isOpen,
  onClose,
  onAssetAdded,
  onShowToast
}) => {
  const [formData, setFormData] = useState({
    asset_identifier: '',
    asset_type: 'Truck',
    current_location: '',
    capacity: 10.0,
    capacity_unit: 'tons',
    is_refrigerated: false,
    status: 'AVAILABLE',
    current_assignment: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.asset_identifier || !formData.current_location) {
      onShowToast('Asset ID and current location are required.', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.createFleetAsset({
        ...formData,
        capacity: Number(formData.capacity)
      });
      onShowToast(`Fleet asset ${formData.asset_identifier} registered successfully.`, 'success');
      onAssetAdded();
      onClose();
    } catch (err: any) {
      onShowToast(`Failed to register asset: ${err.message}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Physical Fleet Asset"
      subtitle="Register trucks, reefer containers, and vessels into the autonomous fleet pool"
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Asset Identifier *</label>
          <input
            type="text"
            placeholder="e.g. TRUCK-205"
            value={formData.asset_identifier}
            onChange={(e) => setFormData({ ...formData, asset_identifier: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Asset Type</label>
            <select
              value={formData.asset_type}
              onChange={(e) => setFormData({ ...formData, asset_type: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="Truck">Truck</option>
              <option value="Container">Container</option>
              <option value="Vessel">Vessel</option>
              <option value="Air Cargo Unit">Air Cargo Unit</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Current Positioning Hub *</label>
            <input
              type="text"
              placeholder="e.g. Ahmedabad"
              value={formData.current_location}
              onChange={(e) => setFormData({ ...formData, current_location: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Payload Capacity</label>
            <input
              type="number"
              step="0.5"
              min="0.5"
              value={formData.capacity}
              onChange={(e) => setFormData({ ...formData, capacity: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Initial Status</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-semibold"
            >
              <option value="AVAILABLE">AVAILABLE</option>
              <option value="IN_TRANSIT">IN TRANSIT</option>
              <option value="IDLE">IDLE</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
            </select>
          </div>
        </div>

        {/* Reefer toggle */}
        <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ThermometerSnowflake className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-semibold text-slate-200">Refrigerated Unit (Cold-Chain Certified)</span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={formData.is_refrigerated}
              onChange={(e) => setFormData({ ...formData, is_refrigerated: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-600"></div>
          </label>
        </div>

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
            {isSubmitting ? 'Registering...' : 'Add Fleet Asset'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
