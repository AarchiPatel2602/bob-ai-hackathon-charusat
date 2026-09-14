import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { DashboardPage } from './pages/DashboardPage';
import { ShipmentsPage } from './pages/ShipmentsPage';
import { DisruptionsPage } from './pages/DisruptionsPage';
import { AlertsPage } from './pages/AlertsPage';
import { FleetPage } from './pages/FleetPage';
import { BobCopilotPage } from './pages/BobCopilotPage';
import { DashboardSummary } from './types';
import { api } from './services/api';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

interface ToastMessage {
  id: number;
  message: string;
  type: 'success' | 'info' | 'error';
}

const MainApp: React.FC = () => {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'signup'>('login');
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  
  // Cross-page navigation state (e.g. click shipment in dashboard -> open in shipments page)
  const [focusedShipmentId, setFocusedShipmentId] = useState<number | null>(null);

  // Global telemetry & summary
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState<boolean>(true);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState<number>(0);

  // Global toasts
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (message: string, type: 'success' | 'info' | 'error' = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const fetchGlobalData = async () => {
    if (!user) return;
    try {
      const [sum, alerts] = await Promise.all([
        api.getDashboardSummary(),
        api.getAlerts({ is_read: false })
      ]);
      setSummary(sum);
      setUnreadAlertsCount(alerts.length);
    } catch {
      // ignore background poll errors
    } finally {
      setIsSummaryLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchGlobalData();
      // Intelligent polling every 8 seconds for real-time telematics
      const interval = setInterval(fetchGlobalData, 8000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleSelectShipment = (id: number) => {
    setFocusedShipmentId(id);
    setCurrentTab('shipments');
  };

  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-[#070b14] flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-medium">Connecting to RouteWise AI Network...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return authView === 'login' ? (
      <LoginPage
        onSwitchToSignup={() => setAuthView('signup')}
        onShowToast={showToast}
      />
    ) : (
      <SignupPage
        onSwitchToLogin={() => setAuthView('login')}
        onShowToast={showToast}
      />
    );
  }

  return (
    <div className="h-screen w-screen flex bg-[#070b14] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        unreadAlertCount={unreadAlertsCount}
      />

      {/* Main Command Center Canvas */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Header
          currentTab={currentTab}
          onRefreshData={fetchGlobalData}
          onShowToast={showToast}
        />

        <main className="flex-1 overflow-y-auto bg-[#070b14]">
          {currentTab === 'dashboard' && (
            <DashboardPage
              summary={summary}
              isLoading={isSummaryLoading}
              onNavigateTab={setCurrentTab}
              onSelectShipment={handleSelectShipment}
            />
          )}

          {currentTab === 'copilot' && (
            <BobCopilotPage />
          )}

          {currentTab === 'shipments' && (
            <ShipmentsPage
              onShowToast={showToast}
              initialSelectedId={focusedShipmentId}
              onClearSelectedId={() => setFocusedShipmentId(null)}
            />
          )}

          {currentTab === 'disruptions' && (
            <DisruptionsPage
              onShowToast={showToast}
              onSelectShipment={handleSelectShipment}
            />
          )}

          {currentTab === 'alerts' && (
            <AlertsPage
              onShowToast={showToast}
              onSelectShipment={handleSelectShipment}
              onAlertsChanged={fetchGlobalData}
            />
          )}

          {currentTab === 'fleet' && (
            <FleetPage
              onShowToast={showToast}
            />
          )}
        </main>
      </div>

      {/* Toast Notification Container */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-2.5 p-3 rounded-xl border text-xs shadow-2xl backdrop-blur-md transition-all duration-300 animate-in fade-in slide-in-from-bottom-2 ${
              t.type === 'success'
                ? 'bg-emerald-950/95 border-emerald-700/80 text-emerald-200'
                : t.type === 'error'
                ? 'bg-rose-950/95 border-rose-700/80 text-rose-200'
                : 'bg-blue-950/95 border-blue-700/80 text-blue-200'
            }`}
          >
            {t.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />}
            {t.type === 'error' && <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
            {t.type === 'info' && <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />}
            <span className="flex-1 font-medium leading-relaxed">{t.message}</span>
            <button
              onClick={() => removeToast(t.id)}
              className="text-slate-400 hover:text-white p-0.5 rounded transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
