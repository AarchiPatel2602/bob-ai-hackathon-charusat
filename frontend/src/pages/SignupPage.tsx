import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, ArrowRight, Lock, Mail, User as UserIcon, Building } from 'lucide-react';

interface SignupPageProps {
  onSwitchToLogin: () => void;
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const SignupPage: React.FC<SignupPageProps> = ({ onSwitchToLogin, onShowToast }) => {
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    organization: 'Global Freight Networks',
    role: 'Logistics Operations Lead'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password.length < 6) {
      onShowToast('Password must be at least 6 characters.', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      await signup(formData);
      onShowToast('Account registered! Initial operational dataset seeded.', 'success');
    } catch (err: any) {
      onShowToast(`Signup failed: ${err.message}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] flex flex-col justify-center items-center p-4 sm:p-6 select-none relative overflow-hidden">
      <div className="w-full max-w-md bg-[#0f172a]/95 border border-slate-800 rounded-2xl shadow-2xl p-8 space-y-6 relative z-10">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 mx-auto">
            <ShieldAlert className="w-7 h-7 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">Create Operator Account</h1>
            <p className="text-xs text-slate-400 mt-1">Connect your supply chain control tower</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
            <div className="relative">
              <UserIcon className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="e.g. Alex Sterling"
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Work Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="alex@freightnet.com"
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition-colors shadow-lg shadow-blue-900/40 flex items-center justify-center gap-1.5"
          >
            <span>{isSubmitting ? 'Registering...' : 'Register Operator Account'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center pt-2 border-t border-slate-800">
          <button
            onClick={onSwitchToLogin}
            className="text-xs text-slate-400 hover:text-blue-400 transition-colors"
          >
            Already have credentials? <span className="font-semibold text-blue-400 underline">Sign In</span>
          </button>
        </div>
      </div>
    </div>
  );
};
