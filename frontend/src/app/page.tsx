"use client";
import { Activity, ArrowUpRight, TrendingUp, AlertTriangle, Wifi, WifiOff } from "lucide-react";
import { useState, useEffect } from "react";

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [feed, setFeed] = useState<string[]>([]);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [totalTracked, setTotalTracked] = useState(0);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/api/stream");
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "raw_feed") {
          setFeed((prev) => {
            const up = [payload.message, ...prev];
            return up.slice(0, 5); // Keep last 5 events
          });
        } else if (payload.type === "prediction_flag") {
          setPredictions((prev) => [payload, ...prev].slice(0, 3));
        } else if (payload.type === "system_status") {
          setTotalTracked(payload.total_matched || 0);
        }
      } catch (e) {}
    };
    return () => ws.close();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Dashboard</h1>
          <p className="text-zinc-400 mt-1">System status and overview</p>
        </div>
        <div className="flex items-center gap-3">
          {isConnected ? (
            <>
              <span className="flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              <span className="text-sm font-medium text-emerald-500 flex items-center gap-1"><Wifi size={14} /> Engine Connected</span>
            </>
          ) : (
            <>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              <span className="text-sm font-medium text-red-500 flex items-center gap-1"><WifiOff size={14} /> Disconnected</span>
            </>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-panel rounded-xl border border-border p-6 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-sm font-medium text-zinc-400">Total Markets Tracked</p>
            <Activity className="text-blue-500" size={20} />
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-white">{totalTracked}</h3>
            <p className="text-sm text-emerald-500 mt-1 flex items-center gap-1">
              <span className="flex items-center"><ArrowUpRight size={14} /> Kalshi & Polymarket Sync</span>
            </p>
          </div>
        </div>
        
        <div className="bg-panel rounded-xl border border-border p-6 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-sm font-medium text-zinc-400">Arbitrage Opportunities</p>
            <AlertTriangle className={predictions.length > 0 ? "text-emerald-500" : "text-amber-500"} size={20} />
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-white">{predictions.length}</h3>
            <p className="text-sm text-zinc-500 mt-1 flex items-center gap-1">
              <span className={predictions.length > 0 ? "text-emerald-400" : "text-zinc-400"}>
                {predictions.length > 0 ? `Spread Detected (${predictions[0].profit_margin}%)` : "Scanner watching ..."}
              </span>
            </p>
          </div>
        </div>

        <div className="bg-panel rounded-xl border border-border p-6 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-sm font-medium text-zinc-400">Smart Wallet Events</p>
            <TrendingUp className="text-emerald-500" size={20} />
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-white">Offline</h3>
            <p className="text-sm text-zinc-500 mt-1 flex items-center gap-1">
              <span className="text-zinc-400">Requires historical processing</span>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-panel rounded-xl border border-border overflow-hidden">
          <div className="p-6 border-b border-border text-emerald-500">
            <h2 className="text-lg font-semibold flex items-center gap-2"><TrendingUp size={16} /> Arbitrage Predictions</h2>
            <p className="text-sm text-zinc-400">Actionable cross-exchange flags</p>
          </div>
          <div className="p-6 min-h-[300px]">
            {predictions.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-zinc-500 pt-16">
                 <AlertTriangle size={32} className="mb-3 opacity-20" />
                 <p>Awaiting Scanner feed...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {predictions.map((p, i) => (
                  <div key={i} className="border border-emerald-900/50 bg-emerald-950/20 p-4 rounded-lg">
                    <div className="flex justify-between items-end mb-2">
                       <span className="font-bold text-emerald-400">{p.ticker}</span>
                       <span className="text-sm bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded">+{p.profit_margin}% margin</span>
                    </div>
                    <p className="text-sm text-zinc-300">Signal: <span className="text-white font-mono">{p.direction}</span></p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="bg-panel rounded-xl border border-border overflow-hidden">
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold text-white">Live Market Data Feed</h2>
            <p className="text-sm text-zinc-400">Parsed from Kalshi & Polymarket webhooks</p>
          </div>
          <div className="p-6 flex flex-col justify-start min-h-[300px] text-zinc-400 font-mono text-xs">
            {feed.length === 0 ? (
               <div className="flex flex-col items-center justify-center pt-16 opacity-50">
                   <Activity size={32} className="mb-3 opacity-50" />
                   <p>Awaiting packets...</p>
               </div>
            ) : (
               <div className="space-y-3">
                 {feed.map((msg, i) => {
                   if (!msg || typeof msg !== "string") return null;
                   return (
                     <div key={i} className={`p-2 rounded border border-border/50 ${msg.includes("Kalshi") ? "bg-blue-900/10 text-blue-400" : "bg-purple-900/10 text-purple-400"}`}>
                       {msg}
                     </div>
                   );
                 })}
               </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
