import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { Incident, IncidentDetail } from "@/types/incident";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(isoDate?: string): string {
  if (!isoDate) return "N/A";
  const date = new Date(isoDate);
  if (isNaN(date.getTime())) return "Invalid Date";
  
  const diff = Date.now() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  if (minutes < 60) return `${minutes}m ${seconds % 60}s ago`;
  if (hours < 24) return `${hours}h ${minutes % 60}m ago`;
  return date.toLocaleDateString();
}

export function formatTimestamp(isoDate: string): string {
  return new Date(isoDate).toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatDate(isoDate?: string): string {
  if (!isoDate) return "N/A";
  const date = new Date(isoDate);
  if (isNaN(date.getTime())) return "Invalid Date";
  
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const formattedDate = `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
  const formattedTime = date.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" });
  return `${formattedDate} · ${formattedTime}`;
}

export function confidenceColor(value: number): string {
  if (value < 0.4) return "text-red-400";
  if (value < 0.7) return "text-amber-400";
  return "text-cyan-400";
}

export function confidenceBgColor(value: number): string {
  if (value < 0.4) return "bg-red-500";
  if (value < 0.7) return "bg-amber-400";
  return "bg-[#00D4FF]";
}

export function confidenceLabel(value: number): string {
  if (value < 0.4) return "Low";
  if (value < 0.7) return "Moderate";
  return "High";
}

export function severityBadgeClass(severity: string): string {
  const base = "px-2 py-0.5 rounded text-[10px] font-bold uppercase border ";
  switch (severity) {
    case "P0": return base + "border-red-500/50 text-red-400 bg-red-500/10";
    case "P1": return base + "border-orange-500/50 text-orange-400 bg-orange-500/10";
    case "P2": return base + "border-amber-500/50 text-amber-400 bg-amber-500/10";
    case "P3": return base + "border-blue-500/50 text-blue-400 bg-blue-500/10";
    default: return base + "border-slate-500/50 text-slate-400 bg-slate-500/10";
  }
}

export function statusBadgeClass(status: string): string {
  const base = "px-2 py-0.5 rounded text-[10px] font-bold uppercase border ";
  switch (status) {
    case "pending": return base + "border-slate-500/50 text-slate-400 bg-slate-500/10";
    case "processing": return base + "border-cyan-500/50 text-cyan-400 bg-cyan-500/10";
    case "completed": return base + "border-green-500/50 text-green-400 bg-green-500/10";
    case "failed": return base + "border-red-500/50 text-red-400 bg-red-500/10";
    default: return base + "border-slate-500/50 text-slate-400 bg-slate-500/10";
  }
}

export function getIncidentTitle(incident: Incident): string {
  return incident.title ?? "Untitled Incident";
}

export function pipelineProgress(incident: IncidentDetail): { completed: number; total: number } {
  return { completed: incident.pipeline_progress, total: 100 };
}
