import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, Sparkles, ArrowRight, Lock, Mail } from 'lucide-react';

interface LoginPageProps {
  onSwitchToSignup: () => void;
  onShowToast: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSwitchToSignup, onShowToast }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('demo@supplyguard.io');
  const [password, setPassword] = useState('SupplyGuard2026!');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await login(email, password);
      onShowToast('Welcome to RouteWise AI Control Tower', 'success');
    } catch (err: any) {
      onShowToast(`Sign in failed: ${err.message}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFillDemo = () => {
    setEmail('demo@supplyguard.io');
    setPassword('SupplyGuard2026!');
    onShowToast('Filled demo logistics manager credentials.', 'info');
  };

  return (
    <div className="min-h-screen bg-[#070b14] flex flex-col justify-center items-center p-4 sm:p-6 select-none relative overflow-hidden">
      {/* Subtle background glow */}
      <div className="absolute w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none -top-20 -left-20" />
      <div className="absolute w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none -bottom-20 -right-20" />

      <div className="w-full max-w-md bg-[#0f172a]/95 border border-slate-800 rounded-2xl shadow-2xl p-8 space-y-6 relative z-10 backdrop-blur-sm">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 mx-auto">
            <ShieldAlert className="w-7 h-7 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center justify-center gap-1.5">
              <h1 className="text-xl font-bold tracking-tight text-white">RouteWise</h1>
              <span className="px-1.5 py-0.5 bg-blue-600 text-white font-bold text-[10px] rounded uppercase tracking-wider">AI 🚢</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">Intelligent Supply Chain Copilot & Resilience Platform</p>
          </div>
        </div>

        {/* Demo Credentials Quick Fill Banner */}
        <div className="p-3 bg-blue-950/40 border border-blue-800/60 rounded-xl flex items-center justify-between text-xs">
          <div className="space-y-0.5">
            <span className="font-bold text-blue-300 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Hackathon Demo Account</span>
            </span>
            <p className="text-[11px] text-slate-400">demo@supplyguard.io • SupplyGuard2026!</p>
          </div>
          <button
            type="button"
            onClick={handleFillDemo}
            className="px-2.5 py-1 bg-blue-600/25 hover:bg-blue-600/40 text-blue-300 border border-blue-500/40 rounded text-[11px] font-semibold transition-colors"
          >
            Auto-fill
          </button>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Work Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@supplyguard.io"
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700/80 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700/80 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition-colors shadow-lg shadow-blue-900/40 flex items-center justify-center gap-1.5"
          >
            <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Control Tower'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Switch to Signup */}
        <div className="text-center pt-2 border-t border-slate-800">
          <button
            onClick={onSwitchToSignup}
            className="text-xs text-slate-400 hover:text-blue-400 transition-colors"
          >
            Don't have an enterprise account? <span className="font-semibold text-blue-400 underline">Register new operator</span>
          </button>
        </div>
      </div>
    </div>
  );
};
