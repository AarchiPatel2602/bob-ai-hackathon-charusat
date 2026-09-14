import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, AlertCircle, ShieldAlert, CheckCircle2, ArrowRight, RefreshCw, Layers } from 'lucide-react';
import { api } from '../services/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'bob';
  text: string;
  timestamp: string;
  data?: {
    finding?: string;
    evidence?: string;
    severity?: string;
    affected_shipments?: string[];
    recommended_action?: string;
    provider_label?: string;
    is_live_ai?: boolean;
    suggested_queries?: string[];
  };
}

const DEFAULT_SUGGESTIONS = [
  "Which shipments are currently at risk?",
  "Which shipment is most urgent?",
  "Why is shipment SH-1024 at risk?",
  "Which cold-chain shipment has exceeded its temperature range?",
  "Should shipment SH-1024 be rerouted?",
  "Which fleet assets are currently idle?",
  "Summarize today's supply-chain risks."
];

export const BobCopilotPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'bob',
      text: "Hello! I am **IBM Bob**, your intelligent supply-chain copilot powered by RouteWise AI. I monitor active corridors, IoT cold-chain telemetry, port disruptions, and fleet availability across your global network.\n\nAsk me about any active shipment, disruption bottleneck, or operational optimization.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      data: {
        provider_label: "RouteWise AI Deterministic Reasoning Engine",
        is_live_ai: false,
        suggested_queries: DEFAULT_SUGGESTIONS
      }
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const response = await api.chatWithBob(q);
      const bobMsg: ChatMessage = {
        id: `bob-${Date.now()}`,
        sender: 'bob',
        text: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        data: {
          finding: response.finding,
          evidence: response.evidence,
          severity: response.severity,
          affected_shipments: response.affected_shipments,
          recommended_action: response.recommended_action,
          provider_label: response.provider_label,
          is_live_ai: response.is_live_ai,
          suggested_queries: response.suggested_queries
        }
      };
      setMessages(prev => [...prev, bobMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'bob',
        text: `⚠️ **Operational Alert:** Unable to process query. ${err.message || 'Please verify backend connection.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-[#070b14] text-slate-100">
      {/* Copilot Header Banner */}
      <div className="px-6 py-4 bg-[#0a101f] border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-400 shadow-inner">
            <Bot className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-tight">IBM Bob Copilot</h2>
              <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-900/60 text-blue-300 border border-blue-700/50">
                watsonx / Granite Ready
              </span>
            </div>
            <p className="text-xs text-slate-400">Conversational L2 Supply Chain Decision Support & MCP Tools</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-3 py-1 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>MCP Context Connected</span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          return (
            <div key={m.id} className={`flex gap-3 max-w-4xl ${isUser ? 'ml-auto flex-row-reverse' : ''}`}>
              <div
                className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-xs font-bold ${
                  isUser
                    ? 'bg-blue-600 text-white'
                    : 'bg-indigo-900/60 text-indigo-300 border border-indigo-700/50'
                }`}
              >
                {isUser ? 'YOU' : <Bot className="w-4 h-4 text-blue-400" />}
              </div>

              <div className={`space-y-2 max-w-2xl ${isUser ? 'items-end' : 'items-start'}`}>
                <div
                  className={`p-4 rounded-xl text-sm leading-relaxed border ${
                    isUser
                      ? 'bg-blue-600 text-white border-blue-500'
                      : 'bg-slate-900/90 text-slate-200 border-slate-800 shadow-md'
                  }`}
                >
                  <div className="whitespace-pre-wrap font-sans text-sm">{m.text}</div>

                  {/* Operational Badges & Rationale */}
                  {m.data?.finding && (
                    <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2 text-xs">
                      {m.data.severity && (
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400 font-medium">Severity:</span>
                          <span
                            className={`px-2 py-0.5 font-bold rounded text-[10px] ${
                              m.data.severity === 'CRITICAL'
                                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                                : m.data.severity === 'HIGH'
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                                : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                            }`}
                          >
                            {m.data.severity}
                          </span>
                        </div>
                      )}
                      {m.data.recommended_action && (
                        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 text-slate-300">
                          <span className="font-bold text-blue-400 block mb-0.5">Recommended Action:</span>
                          {m.data.recommended_action}
                        </div>
                      )}
                      {m.data.provider_label && (
                        <div className="text-[10px] text-slate-500 italic pt-1">
                          Source: {m.data.provider_label} {m.data.is_live_ai ? '(Live API)' : '(Offline Rule Fallback)'}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <span className="text-[10px] text-slate-500 px-1">{m.timestamp}</span>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 max-w-2xl">
            <div className="w-8 h-8 rounded-lg bg-indigo-900/60 border border-indigo-700/50 flex items-center justify-center">
              <Bot className="w-4 h-4 text-blue-400 animate-pulse" />
            </div>
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-sm text-slate-400 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              <span>Querying Model Context Protocol (MCP) data sources & reasoning...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-6 py-2 bg-[#090e1c] border-t border-slate-800/80 overflow-x-auto flex items-center gap-2 shrink-0">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-amber-400" /> Suggested:
        </span>
        {DEFAULT_SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(s)}
            className="px-2.5 py-1 text-xs font-medium rounded-full bg-slate-800/80 hover:bg-blue-900/40 hover:text-blue-300 text-slate-300 border border-slate-700/60 hover:border-blue-700/60 transition-colors whitespace-nowrap"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="p-4 bg-[#0a101f] border-t border-slate-800 flex items-center gap-3 shrink-0">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask Bob about at-risk shipments, temperature alerts, or rerouting..."
          className="flex-1 px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
        />
        <button
          onClick={() => handleSend()}
          disabled={!inputQuery.trim() || isLoading}
          className={`px-5 py-3 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${
            !inputQuery.trim() || isLoading
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/40'
          }`}
        >
          <span>Send</span>
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
