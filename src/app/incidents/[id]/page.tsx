"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getIncident } from "@/lib/api";
import type { IncidentDetail } from "@/types/incident";
import { ActionsCard } from "@/components/ActionsCard";
import { BottomBar } from "@/components/BottomBar";
import { ImpactCard } from "@/components/ImpactCard";
import { MemoryCard } from "@/components/MemoryCard";
import { PipelineTracker } from "@/components/PipelineTracker";
import { RCAPanel } from "@/components/RCAPanel";
import { ScriptCard } from "@/components/ScriptCard";
import { StatusBadge } from "@/components/StatusBadge";
import { TimelinePanel } from "@/components/TimelinePanel";

const POLL_INTERVAL_MS = 3000;
const TERMINAL_STATUSES = new Set(["completed", "failed"]);

export default function IncidentDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const incidentId = params.id;

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncident = useCallback(
    async (isInitial = false): Promise<IncidentDetail | null> => {
      if (!incidentId) return null;

      if (isInitial) {
        setLoading(true);
      }

      try {
        const data = await getIncident(incidentId);
        setIncident(data);
        setError(null);
        return data;
      } catch (cause: unknown) {
        const message = cause instanceof Error ? cause.message : "Failed to load incident.";
        setError(message);
        return null;
      } finally {
        if (isInitial) {
          setLoading(false);
        }
      }
    },
    [incidentId]
  );

  useEffect(() => {
    let isMounted = true;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const run = async () => {
      const firstIncident = await fetchIncident(true);
      if (!isMounted || !firstIncident) return;
      if (TERMINAL_STATUSES.has(firstIncident.status)) return;

      intervalId = setInterval(async () => {
        const latest = await fetchIncident(false);
        if (!latest || TERMINAL_STATUSES.has(latest.status)) {
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
        }
      }, POLL_INTERVAL_MS);
    };

    void run();

    return () => {
      isMounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [fetchIncident]);

  if (loading) {
    return (
      <main className="mx-auto flex h-64 max-w-5xl items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">Loading incident...</p>
      </main>
    );
  }

  if (error || !incident) {
    return (
      <main className="mx-auto flex h-64 max-w-5xl flex-col items-center justify-center gap-4 p-6">
        <p className="text-sm text-destructive">{error ?? "Incident not found."}</p>
        <button
          onClick={() => router.push("/")}
          className="rounded-md border border-border px-3 py-1 text-sm hover:bg-muted"
        >
          Back to incidents
        </button>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-6 pb-24">
      <header className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-xl font-medium">{incident.title}</h1>
          <p className="text-sm text-muted-foreground">ID: {incident.id}</p>
        </div>
        <StatusBadge status={incident.status} />
      </header>

      <PipelineTracker incident={incident} />

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TimelinePanel events={incident.timeline} />
        <RCAPanel hypotheses={incident.hypotheses} />
        {incident.impact && <ImpactCard impact={incident.impact} />}
        <MemoryCard similarIncidents={incident.similar_incidents} />
        <ActionsCard actions={incident.actions} incidentId={incident.id} />
        <ScriptCard incidentId={incident.id} />
      </section>

      <BottomBar incident={incident} />
    </main>
  );
}
