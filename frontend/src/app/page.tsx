"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Send, Shield, AlertTriangle, CheckCircle, Clock, ShoppingCart, Terminal, Zap } from "lucide-react";
import { format } from "date-fns";
import { motion, AnimatePresence } from "framer-motion";

const API_URL = "http://127.0.0.1:8000/api";

type AuditLog = {
  id: number;
  timestamp: string;
  action: string;
  status: string;
  reason: string;
  amount: number;
  cart_details: any;
};

export default function Dashboard() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [messages, setMessages] = useState<{ role: string; content: string; requiresPayment?: boolean; paymentLink?: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sessionId = "sess_demo_001";

  const fetchLogs = async () => {
    try {
      const res = await axios.get(`${API_URL}/audit-logs`);
      setLogs(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, {
        session_id: sessionId,
        message: userMessage.content,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.data.response,
          requiresPayment: res.data.requires_payment,
          paymentLink: res.data.payment_link,
        },
      ]);
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "System error: Unable to process request." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white font-sans selection:bg-purple-500/30">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-xl shadow-[0_0_20px_rgba(168,85,247,0.4)]">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Razorpay AgentGuard
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Policy Engine Active
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-6 grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-90px)]">
        
        {/* Left Column: Merchant Dashboard */}
        <div className="flex flex-col gap-6 h-full">
          
          {/* Policy Studio */}
          <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6 backdrop-blur-sm relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="flex items-center justify-between mb-6 relative">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                Active Policy: "Demo Session"
              </h2>
            </div>
            
            <div className="grid grid-cols-2 gap-4 relative">
              <div className="bg-black/40 border border-white/5 rounded-xl p-4">
                <p className="text-sm text-gray-400 mb-1">Max Transaction Limit</p>
                <p className="text-2xl font-mono font-bold text-emerald-400">₹5,000</p>
              </div>
              <div className="bg-black/40 border border-white/5 rounded-xl p-4">
                <p className="text-sm text-gray-400 mb-1">Blocked Categories</p>
                <div className="flex gap-2 flex-wrap mt-2">
                  <span className="px-2 py-1 text-xs rounded-md bg-red-500/10 text-red-400 border border-red-500/20">Weapons</span>
                  <span className="px-2 py-1 text-xs rounded-md bg-red-500/10 text-red-400 border border-red-500/20">Drugs</span>
                </div>
              </div>
            </div>
          </div>

          {/* Audit Trail */}
          <div className="flex-1 bg-white/[0.02] border border-white/10 rounded-2xl backdrop-blur-sm flex flex-col overflow-hidden">
            <div className="p-4 border-b border-white/10 bg-black/20 flex justify-between items-center">
              <h2 className="font-semibold flex items-center gap-2">
                <Terminal className="w-5 h-5 text-gray-400" />
                Live Audit Trail
              </h2>
              <span className="text-xs text-gray-500 font-mono">Polling 1000ms</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-sm scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              <AnimatePresence>
                {logs.length === 0 ? (
                  <div className="text-gray-500 text-center mt-10">No transactions recorded yet.</div>
                ) : (
                  logs.map((log) => (
                    <motion.div
                      key={log.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-4 rounded-xl border ${
                        log.status === "BLOCKED"
                          ? "bg-red-500/10 border-red-500/30 shadow-[inset_0_0_15px_rgba(239,68,68,0.1)]"
                          : "bg-emerald-500/10 border-emerald-500/30"
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          {log.status === "BLOCKED" ? (
                            <AlertTriangle className="w-4 h-4 text-red-400" />
                          ) : (
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                          )}
                          <span className={log.status === "BLOCKED" ? "text-red-400 font-bold" : "text-emerald-400 font-bold"}>
                            {log.status === "BLOCKED" ? "TRANSACTION INTERCEPTED" : "TRANSACTION APPROVED"}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">{format(new Date(log.timestamp), "HH:mm:ss")}</span>
                      </div>
                      
                      <div className="text-gray-300 mb-2 leading-relaxed">
                        Reason: <span className="text-white">{log.reason}</span>
                      </div>
                      
                      <div className="flex justify-between items-end mt-4 pt-3 border-t border-white/5 text-xs text-gray-400">
                        <div>
                          Amount: <span className="text-white font-bold text-sm">₹{log.amount}</span>
                        </div>
                        <div>
                          Session: {log.session_id}
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Right Column: AI Chat Agent */}
        <div className="bg-[#111] border border-white/10 rounded-2xl flex flex-col overflow-hidden shadow-2xl relative">
          <div className="p-4 border-b border-white/10 bg-black/40 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center">
                <ShoppingCart className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className="font-semibold text-sm">TechStore AI Assistant</h2>
                <p className="text-xs text-gray-400">Ask me to find and add products.</p>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
                <ShoppingCart className="w-12 h-12 opacity-20" />
                <p className="text-sm text-center max-w-xs">
                  Try saying: "Add the flagship gaming laptop to my cart." or "Find a mechanical keyboard under ₹4,000."
                </p>
              </div>
            )}
            
            {messages.map((m, i) => (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl p-4 ${
                    m.role === "user"
                      ? "bg-blue-600 text-white rounded-tr-none"
                      : "bg-white/5 border border-white/10 text-gray-200 rounded-tl-none"
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{m.content}</div>
                  
                  {m.requiresPayment && m.paymentLink && (
                    <a
                      href={m.paymentLink}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-4 block w-full text-center bg-white text-black font-semibold py-2 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Pay via Razorpay
                    </a>
                  )}
                </div>
              </motion.div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-none p-4 flex gap-2">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={sendMessage} className="p-4 border-t border-white/10 bg-black/20">
            <div className="relative flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message the shopping assistant..."
                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-sm transition-all"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="absolute right-2 p-2 rounded-lg bg-white/10 hover:bg-purple-500 text-white transition-colors disabled:opacity-50 disabled:hover:bg-white/10"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>

      </main>
    </div>
  );
}
