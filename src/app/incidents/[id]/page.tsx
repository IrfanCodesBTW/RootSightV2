"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Incident, PipelineState, PIPELINE_STEPS, IncidentStatus, PipelineStepStatus, Severity, Hypothesis, Event } from "@/types";
import type { Hypothesis as HypothesisType } from "@/types";
import {
  formatRelativeTime,
  formatAbsoluteTime,
  getIncidentDuration,
  cn,
} from "@/lib/utils";
import {
  ArrowLeft, Clock, Search, AlertTriangle, Database, Zap,
  Download, CheckCircle2, XCircle, Loader2, Copy, Send,
  Check, ExternalLink, ChevronDown, ChevronUp, LinkIcon,
} from "lucide-react";
import ConfidenceBar from "@/components/shared/ConfidenceBar";
import SeverityIndicator from "@/components/shared/SeverityIndicator";
import { StatusBadge } from "@/components/StatusBadge";

const STEP_ICONS: Record<string, any> = {
  ingestion: Download, timeline: Clock, rca: Search,
  impact: AlertTriangle, memory: Database, actions: Zap,
};

const SEV_COLORS: Record<string, string> = {
  [Severity.P0]: "bg-red-500/10 text-red-400 border-red-500/30",
  [Severity.P1]: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  [Severity.P2]: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  [Severity.P3]: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  [Severity.P4]: "bg-slate-500/10 text-slate-400 border-slate-500/30",
};

const BAND_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 border-red-500/20 text-red-400",
  high: "bg-amber-500/10 border-amber-500/20 text-amber-400",
  medium: "bg-blue-500/10 border-blue-500/20 text-blue-400",
  low: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
};

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const incidentId = params.id as string;
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const fetchIncident = async () => {
    try {
      const res = await api.getIncident(incidentId);
      setIncident(res);
    } catch (e) {
      console.error("Failed to fetch incident:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncident();
    const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
    if (!demoMode) {
      pollRef.current = setInterval(fetchIncident, 3000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [incidentId]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
    </div>
  );

  if (!incident) return (
    <div className="min-h-screen flex items-center justify-center flex-col gap-4">
      <AlertTriangle className="w-12 h-12 text-red-400" />
      <p className="text-gray-400">Incident not found</p>
      <button onClick={() => router.push("/")} className="px-4 py-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/30 hover:bg-blue-500/20 transition-colors">
        Back to Dashboard
      </button>
    </div>
  );

  const incData = incident.incident;
  const pipelineState = incident.pipeline_steps;
  const pipelineKeys = pipelineState ? (Object.keys(pipelineState) as Array<keyof PipelineState>) : [];
  const completedSteps = pipelineState ? pipelineKeys.filter(k => pipelineState[k]?.status === PipelineStepStatus.COMPLETE).length : 0;
  const progressPct = pipelineKeys.length > 0 ? Math.round((completedSteps / pipelineKeys.length) * 100) : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back */}
      <button onClick={() => router.push("/")} className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" />Back to Dashboard
      </button>

      {/* Header Card */}
      <div className="rounded-2xl bg-[#0f0f18] border border-white/[0.07] p-6 mb-6">
        <div className="flex flex-col lg:flex-row lg:items-start gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <span className={cn("text-xs font-bold px-2.5 py-1 rounded-md border font-mono", SEV_COLORS[incData?.severity ?? "P2"])}>
                {incData?.severity ?? "P2"}
              </span>
              <StatusBadge status={incident.status as IncidentStatus} />
              <span className="text-xs font-mono text-gray-500 bg-white/[0.04] px-2 py-1 rounded">
                {(incData?.source ?? "unknown").toUpperCase()}
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight mb-2">{incData?.title ?? "Untitled Incident"}</h1>
            <p className="text-gray-400 text-sm">{incData?.description ?? ""}</p>
          </div>
          <div className="flex gap-8 lg:border-l lg:border-white/[0.07] lg:pl-6">
            {[
              { label: "Duration", val: incident.started_at && incident.completed_at ? getIncidentDuration({ started_at: incident.started_at, completed_at: incident.completed_at } as any) : "Ongoing" },
              { label: "Created", val: formatRelativeTime(incident.started_at || new Date().toISOString()) },
              { label: "Pipeline", val: `${progressPct}%` },
            ].map(({ label, val }) => (
              <div key={label}>
                <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">{label}</div>
                <div className="font-mono text-sm font-semibold">{val}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pipeline Steps */}
      {pipelineState && (
        <div className="rounded-2xl bg-[#0f0f18] border border-white/[0.07] p-6 mb-6">
          <div className="text-[11px] uppercase tracking-widest text-gray-500 font-semibold mb-6 flex items-center gap-2">
            <span className="w-0.5 h-3.5 rounded bg-blue-400 inline-block" />Pipeline Progress
          </div>
          <div className="flex items-start gap-0">
            {PIPELINE_STEPS.map((step, idx) => {
              const stepState = pipelineState[step.key];
              const Icon = STEP_ICONS[step.key];
              const isLast = idx === PIPELINE_STEPS.length - 1;
              const status = stepState?.status || PipelineStepStatus.PENDING;

              return (
                <div key={step.key} className="flex-1 flex flex-col items-center relative">
                  {!isLast && (
                    <div className="absolute top-5 left-1/2 w-full h-0.5 bg-white/[0.07] z-0">
                      {(status === PipelineStepStatus.COMPLETE) && (
                        <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-500/30 transition-all duration-700" />
                      )}
                    </div>
                  )}
                  <div className={cn(
                    "w-10 h-10 rounded-xl flex items-center justify-center relative z-10 transition-all duration-300",
                    status === PipelineStepStatus.COMPLETE && "bg-emerald-500/15 border border-emerald-500/40",
                    status === PipelineStepStatus.RUNNING && "bg-blue-500/15 border border-blue-500/40 animate-pulse",
                    status === PipelineStepStatus.FAILED && "bg-red-500/15 border border-red-500/40",
                    status === PipelineStepStatus.PENDING && "bg-white/[0.04] border border-white/[0.07]",
                  )}>
                    {Icon && <Icon className={cn(
                      "w-4 h-4",
                      status === PipelineStepStatus.COMPLETE && "text-emerald-400",
                      status === PipelineStepStatus.RUNNING && "text-blue-400",
                      status === PipelineStepStatus.FAILED && "text-red-400",
                      status === PipelineStepStatus.PENDING && "text-gray-600",
                    )} />}
                  </div>
                  <div className={cn(
                    "text-[11px] font-semibold mt-2 text-center",
                    status === PipelineStepStatus.COMPLETE && "text-emerald-400",
                    status === PipelineStepStatus.RUNNING && "text-blue-400",
                    status === PipelineStepStatus.PENDING && "text-gray-600",
                  )}>{step.label}</div>
                  <div className="mt-1 text-[9px] py-0.5 px-2 bg-white/[0.04] rounded-full border border-white/[0.07] text-gray-500">
                    {status}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Intelligence Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Timeline */}
        {incident.timeline && incident.timeline.events && incident.timeline.events.length > 0 && (
          <Panel title="Timeline Reconstruction" accent="blue" badge={`${incident.timeline.events.length} events`}>
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {[...incident.timeline.events].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()).map((ev) => (
                <div key={ev.event_id} className="grid grid-cols-[72px_1fr] gap-3 group">
                  <div className="text-[10px] font-mono text-gray-500 pt-2 text-right leading-tight">{formatAbsoluteTime(ev.timestamp)}</div>
                  <div className="bg-white/[0.03] border border-white/[0.06] border-l-2 border-l-blue-500/60 rounded-lg p-3">
                    <p className="text-sm text-gray-200 mb-2">{ev.description}</p>
                    <div className="flex flex-wrap gap-1 mb-2">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.04] text-gray-500">{ev.evidence_source}</span>
                    </div>
                    <ConfidenceBar confidence={ev.confidence} />
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        )}

        {/* RCA Hypotheses */}
        {incident.rca && (incident.rca.hypotheses?.length > 0 || incident.rca.insufficient_data) && (
          <Panel title="RCA Hypotheses" accent="purple" badge={incident.rca.insufficient_data ? "Insufficient Data" : `${incident.rca.hypotheses.length} hypotheses`}>
            {incident.rca.insufficient_data ? (
              <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400 text-sm flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <p>Insufficient data to generate reliable root cause hypotheses (requires at least 3 events). Please ingest more logs or events.</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {incident.rca.hypotheses.map((h, index) => (
                  <HypothesisCard
                    key={h.id}
                    hypothesis={h}
                    index={index}
                    events={incident.timeline?.events || []}
                  />
                ))}
              </div>
            )}
          </Panel>
        )}

        {/* Impact */}
        {incident.impact && (
          <Panel title="Impact Analysis" accent="red">
            <div className={cn("flex items-center gap-3 p-4 rounded-xl border mb-4", BAND_COLORS[incident.impact.severity_band])}>
              <div className="text-2xl">{incident.impact.severity_band === "critical" ? "🔴" : incident.impact.severity_band === "high" ? "🟠" : "🟡"}</div>
              <div>
                <div className="text-[10px] uppercase tracking-widest font-semibold mb-0.5 opacity-70">Severity Band</div>
                <div className="text-xl font-bold uppercase">{incident.impact.severity_band}</div>
              </div>
            </div>
            {(incident.impact.affected_users > 0 || incident.impact.estimated_requests_affected) && (
              <div className="grid grid-cols-2 gap-3 mb-4">
                {incident.impact.affected_users > 0 && (
                  <div className="bg-amber-500/[0.07] border border-amber-500/20 rounded-xl p-3">
                    <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">Users Affected</div>
                    <div className="font-mono text-xl font-bold text-amber-400">{incident.impact.affected_users.toLocaleString()}</div>
                  </div>
                )}
                {incident.impact.estimated_requests_affected && (
                  <div className="bg-red-500/[0.07] border border-red-500/20 rounded-xl p-3">
                    <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">Requests Affected</div>
                    <div className="font-mono text-xl font-bold text-red-400">{incident.impact.estimated_requests_affected}</div>
                  </div>
                )}
              </div>
            )}
            <ImpactRow label="Business Impact" text={incident.impact.business_impact_summary ?? "Not yet assessed"} />
            <ImpactRow label="User Impact" text={incident.impact.probable_user_impact ?? "Unknown"} />
            <div>
              <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">Affected Services</div>
              <div className="flex flex-wrap gap-1.5">
                {incident.impact.affected_services.map(s => (
                  <span key={s} className="font-mono text-[11px] px-2 py-1 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">{s}</span>
                ))}
              </div>
            </div>
          </Panel>
        )}

        {/* Similar Incidents */}
        {incident.memory && incident.memory.matches && incident.memory.matches.length > 0 && (
          <Panel title="Similar Incidents" accent="cyan" badge="via FAISS">
            <div className="space-y-3">
              {incident.memory.matches.map(s => (
                <div key={`${s.incident_id}-${s.similar_to_id}`} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 hover:border-white/[0.12] transition-colors">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="font-semibold text-sm">{s.similar_to_id}</div>
                    <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded-md bg-cyan-500/15 text-cyan-400 flex-shrink-0">
                      {Math.round(s.similarity_score * 100)}% match
                    </span>
                  </div>
                  <p className="text-[12px] text-gray-400 italic border-l-2 border-cyan-500/40 pl-3 mb-3">{s.why_similar}</p>
                  <div className="flex items-start gap-2 text-emerald-400 text-[12px]">
                    <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span>{s.previous_fix}</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        )}

        {/* Actions — full width */}
        {incident.actions && incident.actions.actions && incident.actions.actions.length > 0 && (
          <div className="lg:col-span-2">
            <Panel title="Generated Actions" accent="amber">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {incident.actions.actions.map(action => (
                  <ActionCard key={action.action_id} action={action} />
                ))}
              </div>
            </Panel>
          </div>
        )}

        {/* Empty state if pipeline still running */}
        {(!incident.timeline || !incident.timeline.events || incident.timeline.events.length === 0) &&
         (!incident.rca || !incident.rca.hypotheses || incident.rca.hypotheses.length === 0) && (
          <div className="lg:col-span-2 rounded-2xl bg-[#0f0f18] border border-white/[0.07] p-16 text-center">
            <Loader2 className="w-10 h-10 animate-spin text-blue-400 mx-auto mb-4" />
            <div className="text-lg font-semibold mb-2">Pipeline Running</div>
            <div className="text-sm text-gray-500">Intelligence outputs appear as each stage completes. Polling every 3s…</div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Sub-components ── */

function Panel({ title, accent, badge, children }: { title: string; accent: string; badge?: string; children: React.ReactNode }) {
  const accentColors: Record<string, string> = {
    blue: "bg-blue-400", purple: "bg-purple-400", red: "bg-red-400",
    cyan: "bg-cyan-400", amber: "bg-amber-400", green: "bg-emerald-400",
  };
  return (
    <div className="rounded-2xl bg-[#0f0f18] border border-white/[0.07] p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-gray-500 font-semibold">
          <span className={cn("w-0.5 h-3.5 rounded inline-block", accentColors[accent] || "bg-blue-400")} />
          {title}
        </div>
        {badge && <span className="text-[10px] text-gray-500 font-mono">{badge}</span>}
      </div>
      {children}
    </div>
  );
}

function ImpactRow({ label, text }: { label: string; text: string }) {
  return (
    <div className="mb-4">
      <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-1.5">{label}</div>
      <p className="text-sm text-gray-300 leading-relaxed">{text}</p>
    </div>
  );
}

const EVIDENCE_BORDER_COLORS: Record<string, string> = {
  strong: "border-l-teal-500",
  moderate: "border-l-amber-500",
  weak: "border-l-gray-500",
};

const EVIDENCE_BADGE_COLORS: Record<string, string> = {
  strong: "bg-teal-500/15 text-teal-400",
  moderate: "bg-amber-500/15 text-amber-400",
  weak: "bg-gray-500/15 text-gray-400",
};

function HypothesisCard({ hypothesis: h, index, events }: { hypothesis: HypothesisType; index: number; events: Event[] }) {
  const [expanded, setExpanded] = useState(false);
  const strength = h.evidence_strength || "weak";
  const eventCount = h.supporting_event_ids?.length || 0;

  // Resolve cited event IDs to their actual event objects from the timeline
  const resolvedEvents = (h.supporting_event_ids || []).map(id => {
    const found = events.find(e => e.event_id === id);
    return found ? { id, description: found.description, source: found.evidence_source, type: found.event_type } : { id, description: null, source: null, type: null };
  });

  return (
    <div className={cn(
      "bg-white/[0.03] border border-white/[0.06] border-l-[3px] rounded-xl p-4 hover:border-white/[0.12] transition-all",
      EVIDENCE_BORDER_COLORS[strength],
    )}>
      <div className="flex items-start gap-3 mb-2">
        <span className={cn("w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold font-mono flex-shrink-0 mt-0.5",
          index === 0 ? "bg-amber-500/20 text-amber-400" : "bg-white/[0.06] text-gray-500")}>
          #{index + 1}
        </span>
        <div className="flex-1">
          <div className="flex items-start justify-between gap-2 mb-1">
            <span className="font-semibold text-sm">{h.text}</span>
            <span className={cn("font-mono text-[11px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-md flex-shrink-0",
              h.confidence === "high" ? "bg-teal-500/15 text-teal-400" :
              h.confidence === "medium" ? "bg-blue-500/15 text-blue-400" : "bg-amber-500/15 text-amber-400"
            )}>{h.confidence}</span>
          </div>
          <div className="flex items-center flex-wrap gap-2 mb-2">
            <span className="font-semibold text-gray-300 uppercase text-[10px] bg-white/[0.05] px-1.5 py-0.5 rounded">
              {h.category}
            </span>
            <span className={cn("text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded-md", EVIDENCE_BADGE_COLORS[strength])}>
              {strength}
            </span>
            <span className="text-xs text-gray-400">{h.recommended_action_hint}</span>
          </div>
        </div>
      </div>

      {/* Evidence anchor footer */}
      {eventCount > 0 && (
        <div className="mt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer group"
          >
            <LinkIcon className="w-3 h-3" />
            Supported by {eventCount} event{eventCount !== 1 ? "s" : ""}
            {expanded ? <ChevronUp className="w-3 h-3 ml-0.5" /> : <ChevronDown className="w-3 h-3 ml-0.5" />}
          </button>

          {expanded && (
            <div className="mt-2.5 space-y-2 pl-3 border-l-2 border-emerald-500/30 animate-in fade-in slide-in-from-top-1 duration-200">
              {resolvedEvents.map((ev) => (
                <div key={ev.id} className="bg-white/[0.02] border border-white/[0.05] rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">{ev.id}</span>
                    {ev.type && <span className="text-[10px] text-gray-500 font-mono">{ev.type}</span>}
                    {ev.source && <span className="text-[10px] text-gray-600 font-mono">via {ev.source}</span>}
                  </div>
                  <p className="text-[12px] text-gray-300 leading-relaxed">
                    {ev.description || <span className="italic text-gray-600">Event not found in timeline</span>}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ActionCard({ action }: { action: any }) {
  const [approval, setApproval] = useState(action.approval_status);
  const [copied, setCopied] = useState(false);
  const typeIcons: Record<string, string> = { slack_responder: "💬", jira_ticket: "📋", manual_review: "📝" };

  const handleCopy = () => {
    navigator.clipboard.writeText(action.payload_preview || JSON.stringify(action.full_payload)).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <span>{typeIcons[action.action_type] || "📄"}</span>
          <span className="font-semibold text-sm capitalize">{action.action_type?.replace(/_/g, " ")}</span>
        </div>
        <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded-full",
          approval?.includes("pending") && "bg-amber-500/15 text-amber-400",
          approval === "approved" && "bg-emerald-500/15 text-emerald-400",
          approval === "rejected" && "bg-red-500/15 text-red-400",
        )}>{approval}</span>
      </div>
      <pre className="px-4 py-3 text-[11px] font-mono text-gray-400 leading-relaxed overflow-y-auto max-h-44 whitespace-pre-wrap">
        {action.payload_preview}
      </pre>
      <div className="flex items-center justify-end gap-2 px-4 py-2.5 border-t border-white/[0.06]">
        <button onClick={handleCopy} className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-lg border border-white/[0.07] text-gray-400 hover:text-gray-200 hover:bg-white/[0.05] transition-all">
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
        <button onClick={() => setApproval("approved")} className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-all">
          <CheckCircle2 className="w-3 h-3" />Approve
        </button>
        <button className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 hover:bg-blue-500/20 transition-all">
          <Send className="w-3 h-3" />Send
        </button>
      </div>
    </div>
  );
}
