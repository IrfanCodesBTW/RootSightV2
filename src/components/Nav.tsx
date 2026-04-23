"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { checkHealth, listIncidents } from "@/lib/api";
import { useLayout } from "@/app/layout-client";
import { cn } from "@/lib/utils";

export function Nav() {
  const { openTriggerModal } = useLayout();
  const [health, setHealth] = useState<"healthy" | "error" | "loading">("loading");
  const [activeCount, setActiveCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      // Health check
      try {
        const res = await checkHealth();
        setHealth(res.status === "healthy" ? "healthy" : "error");
      } catch (err: unknown) {
        console.error(err);
        setHealth("error");
      }

      // Active incidents count
      try {
        const incidents = await listIncidents();
        const active = incidents.filter((i) => i.status === "processing" || i.status === "pending").length;
        setActiveCount(active);
      } catch (err: unknown) {
        console.error(err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="fixed top-0 left-0 right-0 h-14 bg-[#0A0A0F] border-b border-[--border] z-50 flex items-center justify-between px-6">
      {/* Left Side */}
      <Link href="/" className="flex items-center gap-2 group">
        <span className="font-mono font-bold tracking-widest text-lg flex">
          <span className="text-[--accent] [text-shadow:0_0_10px_var(--accent-dim)]">ROOT</span>
          <span className="text-white">SIGHT</span>
        </span>
      </Link>

      {/* Right Side */}
      <div className="flex items-center gap-4">
        {activeCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1 bg-[--accent-dim] border border-[--accent]/30 rounded-full">
            <span className="w-1.5 h-1.5 bg-[--accent] rounded-full animate-pulse" />
            <span className="text-[10px] font-bold text-[--accent] uppercase tracking-wider">
              {activeCount} active
            </span>
          </div>
        )}

        <div className="flex items-center gap-2 px-2 py-1 bg-white/[0.02] border border-[--border] rounded-md">
          <div className={cn(
            "w-2 h-2 rounded-full transition-all duration-500",
            health === "healthy" ? "bg-green-500 animate-pulse" : 
            health === "error" ? "bg-red-500" : "bg-slate-500"
          )} />
        </div>

        <button
          onClick={openTriggerModal}
          className="bg-[--accent] text-black font-bold text-sm px-4 py-1.5 rounded-md hover:brightness-110 transition-all active:scale-95"
        >
          New Incident
        </button>
      </div>
    </nav>
  );
}
