import { useState } from "react";
import type { Hypothesis, Event } from "@/types";
import { cn } from "@/lib/utils";

interface RCAPanelProps {
  hypotheses: Hypothesis[];
  insufficientData?: boolean;
  events?: Event[];
}

const EVIDENCE_BORDER: Record<string, string> = {
  strong: "border-l-teal-500",
  moderate: "border-l-amber-500",
  weak: "border-l-gray-500",
};

const EVIDENCE_BADGE: Record<string, string> = {
  strong: "bg-teal-500/10 text-teal-500 border-teal-500/20",
  moderate: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  weak: "bg-gray-500/10 text-gray-500 border-gray-500/20",
};

const confidenceColors: Record<string, string> = {
  high: "bg-teal-500/10 text-teal-500 border-teal-500/20",
  medium: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  low: "bg-amber-500/10 text-amber-500 border-amber-500/20",
};

export function RCAPanel({ hypotheses, insufficientData, events = [] }: RCAPanelProps) {
  if (insufficientData) {
    return (
      <section className="rounded-xl border border-border p-4">
        <p className="text-sm font-medium">Root Cause Analysis</p>
        <p className="mt-2 text-sm text-yellow-500">Insufficient data to generate reliable root cause hypotheses (requires at least 3 events).</p>
      </section>
    );
  }

  if (!hypotheses || hypotheses.length === 0) {
    return (
      <section className="rounded-xl border border-border p-4">
        <p className="text-sm font-medium">Root Cause Analysis</p>
        <p className="mt-2 text-sm text-muted-foreground">No hypotheses generated.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4 rounded-xl border border-border p-4">
      <p className="text-sm font-medium">Root Cause Analysis</p>
      {hypotheses.map((hypothesis, index) => (
        <HypothesisCard
          key={hypothesis.id}
          hypothesis={hypothesis}
          index={index}
          events={events}
        />
      ))}
    </section>
  );
}

function HypothesisCard({ hypothesis, index, events }: { hypothesis: Hypothesis; index: number; events: Event[] }) {
  const [expanded, setExpanded] = useState(false);
  const strength = hypothesis.evidence_strength || "weak";
  const eventCount = hypothesis.supporting_event_ids?.length || 0;

  const resolvedEvents = (hypothesis.supporting_event_ids || []).map(id => {
    const found = events.find(e => e.event_id === id);
    return found
      ? { id, description: found.description, source: found.evidence_source, type: found.event_type }
      : { id, description: null, source: null, type: null };
  });

  return (
    <article className={cn(
      "space-y-2 border-l-[3px] rounded-lg p-3",
      EVIDENCE_BORDER[strength],
    )}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium">
          #{index + 1} {hypothesis.text}
        </p>
        <div className={cn("px-2 py-0.5 rounded-md border text-xs font-semibold uppercase tracking-wider", confidenceColors[hypothesis.confidence] || confidenceColors.low)}>
          {hypothesis.confidence}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span className="font-semibold px-1.5 py-0.5 bg-secondary rounded text-secondary-foreground uppercase">
          {hypothesis.category}
        </span>
        <span className={cn("px-1.5 py-0.5 rounded-md border text-xs font-semibold uppercase", EVIDENCE_BADGE[strength])}>
          {strength}
        </span>
        <span className="px-1.5 py-0.5">
          Action: {hypothesis.recommended_action_hint}
        </span>
      </div>

      {eventCount > 0 && (
        <div className="mt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-semibold text-teal-500 hover:text-teal-400 transition-colors cursor-pointer"
          >
            Supported by {eventCount} event{eventCount !== 1 ? "s" : ""} {expanded ? "▲" : "▼"}
          </button>

          {expanded && (
            <div className="mt-2 space-y-1.5 pl-3 border-l-2 border-teal-500/30">
              {resolvedEvents.map((ev) => (
                <div key={ev.id} className="text-xs bg-muted/50 rounded p-2">
                  <span className="font-mono text-teal-500">{ev.id}</span>
                  {ev.type && <span className="ml-2 text-muted-foreground">[{ev.type}]</span>}
                  {ev.source && <span className="ml-1 text-muted-foreground">via {ev.source}</span>}
                  <p className="mt-0.5 text-foreground/80">
                    {ev.description || <span className="italic text-muted-foreground">Event not found in timeline</span>}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </article>
  );
}
