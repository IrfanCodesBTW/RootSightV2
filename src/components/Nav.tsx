"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useLayout } from "@/app/layout-client";
import { cn } from "@/lib/utils";
import { Zap, Activity } from "lucide-react";
import { IncidentStatus } from "@/types";

export function Nav() {
  const { openTriggerModal } = useLayout();
  const [health, setHealth] = useState<"healthy" | "error" | "loading">("loading");
  const [activeCount, setActiveCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      // Health check
      try {
        const res = await api.checkBackendHealth();
        setHealth(res.healthy ? "healthy" : "error");
      } catch (err: unknown) {
        setHealth("error");
      }

      // Active incidents count
      try {
        const res = await api.listIncidents();
        const active = res.items.filter((i) => 
          i.status !== IncidentStatus.COMPLETED
        ).length;
        setActiveCount(active);
      } catch (err: unknown) {
        console.error("Nav fetch incidents error:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-[#08080d]/80 backdrop-blur-xl border-b border-white/[0.07] z-50 px-6 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-3 group">
        <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
          <Zap className="w-5 h-5 text-white fill-current" />
        </div>
        <div>
          <div className="font-bold text-lg tracking-tight text-white leading-none">RootSight</div>
          <div className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">AI Intelligence</div>
        </div>
      </Link>

      <nav className="flex items-center gap-6">
        <div className="hidden md:flex items-center gap-6 mr-6 border-r border-white/10 pr-6">
          <Link href="/" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Dashboard</Link>
          <a href="#" className="text-sm font-medium text-gray-500 hover:text-white transition-colors cursor-not-allowed">Knowledge Base</a>
          <a href="#" className="text-sm font-medium text-gray-500 hover:text-white transition-colors cursor-not-allowed">Analytics</a>
        </div>

        <div className="flex items-center gap-4">
          {activeCount > 0 && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full">
              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
              <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">
                {activeCount} active
              </span>
            </div>
          )}

          <div className="flex items-center gap-2 px-2.5 py-1.5 bg-white/[0.03] border border-white/10 rounded-lg">
            <div className={cn(
              "w-2 h-2 rounded-full",
              health === "healthy" ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : 
              health === "error" ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" : "bg-gray-600"
            )} />
            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Engine</span>
          </div>

          <button
            onClick={openTriggerModal}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm px-4 py-2 rounded-xl transition-all active:scale-95 shadow-lg shadow-blue-600/20"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span className="hidden sm:inline">Trigger Incident</span>
          </button>
        </div>
      </nav>
    </header>
  );
}
