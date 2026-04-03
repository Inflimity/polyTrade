import Link from "next/link";
import { Home, Activity, Crosshair, Wallet, Settings } from "lucide-react";

export default function Sidebar() {
  return (
    <aside className="w-64 bg-panel border-r border-border flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-tight">Alpha Engine</h1>
        <p className="text-sm text-zinc-400 mt-1">Prediction Markets</p>
      </div>
      <nav className="flex-1 px-4 space-y-2 mt-4">
        <Link href="/" className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-zinc-800 text-white font-medium">
          <Home size={18} />
          <span>Dashboard</span>
        </Link>
        <Link href="/arbitrage" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-colors">
          <Crosshair size={18} />
          <span>Arbitrage Scanner</span>
        </Link>
        <Link href="/smart-money" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-colors">
          <Wallet size={18} />
          <span>Smart Money</span>
        </Link>
        <Link href="/live" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-colors">
          <Activity size={18} />
          <span>Live Feed</span>
        </Link>
      </nav>
      <div className="p-4 border-t border-border">
        <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-colors w-full">
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
}
