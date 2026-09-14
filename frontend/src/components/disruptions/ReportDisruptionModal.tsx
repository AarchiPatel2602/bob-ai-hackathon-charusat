import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../services/api';
import { AlertTriangle } from 'lucide-react';

interface ReportDisruptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDisruptionReported: () => void;
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const ReportDisruptionModal: React.FC<ReportDisruptionModalProps> = ({
  isOpen,
  onClose,
  onDisruptionReported,
  onShowToast
}) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'Port Strike',
    location: '',
    severity: 'HIGH',
    expected_duration_days: 4.0,
    description: '',
    status: 'ACTIVE'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const disruptionTypes = [
    'Port Strike',
    'Port Closure',
    'Storm',
    'Flood',
    'Severe Weather',
    'Road Closure',
    'Rail Disruption',
    'Geopolitical Crisis',
    'Carrier Failure',
    'Other'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.location) {
      onShowToast('Disruption name and geographic location are required.', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        ...formData,
        expected_duration_days: Number(formData.expected_duration_days)
      };

      const res = await api.reportDisruption(payload);
      onShowToast(
        `Disruption reported! Automatic impact analysis identified ${res.affected_shipments_count} affected shipments ($${res.cargo_value_at_risk.toLocaleString()} at risk).`,
        'success'
      );
      onDisruptionReported();
      onClose();
    } catch (err: any) {
      onShowToast(`Failed to report disruption: ${err.message}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Report Supply Chain Disruption"
      subtitle="Immediately initiates impact analysis across active consignments and re-evaluates risk"
      maxWidth="xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Disruption Event Name *</label>
          <input
            type="text"
            placeholder="e.g. Mumbai Port Strike"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-medium"
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Disruption Type</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {disruptionTypes.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Affected Location / Hub *</label>
            <input
              type="text"
              placeholder="e.g. Mumbai Port"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Severity Level</label>
            <select
              value={formData.severity}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-bold"
            >
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Expected Duration (Days)</label>
            <input
              type="number"
              step="0.5"
              min="0.5"
              value={formData.expected_duration_days}
              onChange={(e) => setFormData({ ...formData, expected_duration_days: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Situation Description</label>
          <textarea
            rows={3}
            placeholder="Operational notes, strike conditions, or weather forecasts..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
          />
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
            className="px-5 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-lg transition-colors shadow-lg shadow-rose-900/30 flex items-center gap-1.5"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>{isSubmitting ? 'Analyzing Impact...' : 'Report & Trigger Analysis'}</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
