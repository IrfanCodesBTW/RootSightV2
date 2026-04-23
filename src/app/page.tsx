"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Incident, ListIncidentsResponse, IncidentStatus, PipelineStepStatus, Severity } from "@/types";
import { formatRelativeTime, cn } from "@/lib/utils";
import { 
  Zap, AlertTriangle, CheckCircle2, Clock, 
  ArrowRight, RefreshCw, BarChart3, Activity 
} from "lucide-react";
import SeverityIndicator from "@/components/shared/SeverityIndicator";
import { StatusBadge } from "@/components/StatusBadge";

export default function DashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    resolved: 0,
    avgPipeline: 0
  });

  const fetchIncidents = useCallback(async () => {
    try {
      const res: ListIncidentsResponse = await api.listIncidents(1, 50);
      setIncidents(res.items);
      
      const active = res.items.filter(i => i.status !== IncidentStatus.COMPLETED).length;
      const resolved = res.items.filter(i => i.status === IncidentStatus.COMPLETED).length;
      
      // Calculate avg pipeline progress
      const totalProgress = res.items.reduce((acc, inc) => {
        return acc + calculateProgress(inc);
      }, 0);
      
      setStats({
        total: res.total,
        active,
        resolved,
        avgPipeline: Math.round(totalProgress / (res.items.length || 1))
      });
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 10000);
    return () => clearInterval(interval);
  }, [fetchIncidents]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Incident Dashboard</h1>
          <p className="text-gray-400">Real-time AI pipeline intelligence • Powered by Gemini + RootSight Engine</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => { setLoading(true); fetchIncidents(); }}
            className="p-2.5 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-all"
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard 
          label="Total Incidents" 
          value={stats.total} 
          icon={BarChart3} 
          color="blue" 
        />
        <StatCard 
          label="Active" 
          value={stats.active} 
          icon={AlertTriangle} 
          color="red" 
        />
        <StatCard 
          label="Resolved" 
          value={stats.resolved} 
          icon={CheckCircle2} 
          color="green" 
        />
        <StatCard 
          label="Avg Pipeline %" 
          value={`${stats.avgPipeline}%`} 
          icon={Activity} 
          color="amber" 
        />
      </div>

      {/* Incident Table */}
      <div className="rounded-2xl bg-[#0f0f18] border border-white/[0.07] overflow-hidden shadow-2xl">
        <div className="px-6 py-4 border-b border-white/[0.07] flex items-center justify-between">
          <h2 className="font-semibold text-white">Recent Incidents</h2>
          <div className="text-[10px] text-gray-500 font-mono">Auto-refreshing every 10s</div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/[0.02] text-[10px] uppercase tracking-widest text-gray-500 font-bold border-b border-white/[0.07]">
                <th className="px-6 py-4">Incident</th>
                <th className="px-6 py-4">Severity</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Pipeline</th>
                <th className="px-6 py-4">Created</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {loading && incidents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-20 text-center">
                    <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
                    <p className="text-gray-500">Fetching incidents...</p>
                  </td>
                </tr>
              ) : incidents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-20 text-center text-gray-500">
                    No incidents found.
                  </td>
                </tr>
              ) : (
                incidents.map((incident) => {
                  const id = incident.incident_id;
                  const incData = incident.incident;
                  const title = incData?.title ?? "Untitled Incident";
                  const severity = incData?.severity ?? "P2";
                  return (
                    <tr key={id} className="group hover:bg-white/[0.02] transition-colors cursor-pointer">
                      <td className="px-6 py-4" onClick={() => window.location.href = `/incidents/${id}`}>
                        <div className="font-medium text-gray-200 group-hover:text-white transition-colors">{title}</div>
                        <div className="text-[10px] font-mono text-gray-500 mt-1 uppercase">{id}</div>
                      </td>
                      <td className="px-6 py-4">
                        <SeverityIndicator severity={severity as Severity} />
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={incident.status as IncidentStatus} />
                      </td>
                      <td className="px-6 py-4">
                        <PipelineMini progress={calculateProgress(incident)} />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatRelativeTime(incident.started_at || new Date().toISOString())}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link 
                          href={`/incidents/${id}`}
                          className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-white/[0.04] border border-white/5 text-gray-400 group-hover:text-blue-400 group-hover:bg-blue-500/10 group-hover:border-blue-500/20 transition-all"
                        >
                          <ArrowRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: any; color: string }) {
  const colors: Record<string, string> = {
    blue: "text-blue-400 border-blue-500/20 bg-blue-500/5",
    red: "text-red-400 border-red-500/20 bg-red-500/5",
    green: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    amber: "text-amber-400 border-amber-500/20 bg-amber-500/5",
  };

  return (
    <div className={cn("p-6 rounded-2xl border flex flex-col gap-3", colors[color])}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-widest font-bold opacity-70">{label}</span>
        <Icon className="w-4 h-4 opacity-50" />
      </div>
      <div className="text-3xl font-bold tracking-tighter text-white">{value}</div>
    </div>
  );
}

function PipelineMini({ progress }: { progress: number }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-24 h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-1000" 
          style={{ width: `${progress}%` }} 
        />
      </div>
      <span className="text-[10px] font-mono font-bold text-gray-500 min-w-[28px]">{progress}%</span>
    </div>
  );
}

function calculateProgress(incident: Incident) {
  if (!incident.pipeline_steps) return 0;
  const steps = Object.values(incident.pipeline_steps);
  if (steps.length === 0) return 0;
  const completed = steps.filter(s => s?.status === PipelineStepStatus.COMPLETE).length;
  return Math.round((completed / steps.length) * 100);
}
