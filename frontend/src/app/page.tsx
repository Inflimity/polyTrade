"use client";
import { Activity, ArrowUpRight, TrendingUp, AlertTriangle, Wifi, WifiOff } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function Home() {
  // Connect to the FastAPI backend layer we built in Phase 3
  const { data, isConnected } = useWebSocket("ws://localhost:8000/api/stream");

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
            <h3 className="text-3xl font-bold text-white">—</h3>
            <p className="text-sm text-zinc-500 mt-1 flex items-center gap-1">
              <span className="text-blue-500 flex items-center"><ArrowUpRight size={14} /> Pending integration</span>
            </p>
          </div>
        </div>
        
        <div className="bg-panel rounded-xl border border-border p-6 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-sm font-medium text-zinc-400">Arbitrage Opportunities</p>
            <AlertTriangle className="text-amber-500" size={20} />
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-white">0</h3>
            <p className="text-sm text-zinc-500 mt-1 flex items-center gap-1">
              <span className="text-zinc-400">Scanner initializing</span>
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
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold text-white">Latest Arbitrage Flags</h2>
            <p className="text-sm text-zinc-400">Kalshi vs Polymarket spreads</p>
          </div>
          <div className="p-6 flex flex-col items-center justify-center min-h-[300px] text-zinc-500">
            <AlertTriangle size={32} className="mb-3 opacity-20" />
            <p>{data ? `Latest event: ${JSON.stringify(data.source)}` : "Awaiting Scanner feed..."}</p>
          </div>
        </section>

        <section className="bg-panel rounded-xl border border-border overflow-hidden">
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold text-white">Recent Smart Money Feed</h2>
            <p className="text-sm text-zinc-400">Live trades from top wallets</p>
          </div>
          <div className="p-6 flex flex-col items-center justify-center min-h-[300px] text-zinc-500">
            <Activity size={32} className="mb-3 opacity-20" />
            <p>Awaiting Phase 1 implementation.</p>
          </div>
        </section>
      </div>
    </div>
  );
}
