"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { TriggerModal } from "@/components/TriggerModal";
import { listIncidents, triggerIncident } from "@/lib/api";
import type { Incident, TriggerPayload } from "@/types/incident";

const REFRESH_INTERVAL_MS = 5000;

export default function HomePage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [isDemoRunning, setIsDemoRunning] = useState(false);

  const refreshIncidents = useCallback(async () => {
    try {
      const data = await listIncidents();
      setIncidents(data);
      setError(null);
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Failed to load incidents.");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    listIncidents()
      .then((data) => {
        if (cancelled) return;
        setIncidents(data);
        setError(null);
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setError(cause instanceof Error ? cause.message : "Failed to load incidents.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const hasActiveIncidents = incidents.some(
    (incident) => incident.status === "pending" || incident.status === "processing"
  );

  useEffect(() => {
    if (!hasActiveIncidents) return;

    const intervalId = setInterval(() => {
      void refreshIncidents();
    }, REFRESH_INTERVAL_MS);

    return () => clearInterval(intervalId);
  }, [hasActiveIncidents, refreshIncidents]);

  const runDemo = useCallback(async () => {
    setIsDemoRunning(true);
    setError(null);
    try {
      const payload: TriggerPayload = {
        title: "Demo: High error rate on payment service",
        source: "manual",
        severity: "high",
      };
      await triggerIncident(payload);
      await refreshIncidents();
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Failed to run demo.");
    } finally {
      setIsDemoRunning(false);
    }
  }, [refreshIncidents]);

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-medium">Incidents</h1>
        <div className="flex gap-2">
          <button
            onClick={() => void runDemo()}
            disabled={isDemoRunning}
            className="rounded-md border border-border px-3 py-1.5 text-sm transition-colors hover:bg-muted disabled:opacity-50"
          >
            {isDemoRunning ? "Running..." : "Run Demo"}
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground"
          >
            Trigger Incident
          </button>
        </div>
      </div>

      {loading && (
        <p className="py-10 text-center text-sm text-muted-foreground">Loading incidents...</p>
      )}

      {!loading && error && (
        <p className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
          {error}
        </p>
      )}

      {!loading && incidents.length === 0 && !error && (
        <p className="py-10 text-center text-sm text-muted-foreground">
          No incidents yet. Trigger one or run the demo.
        </p>
      )}

      {!loading && incidents.length > 0 && (
        <div className="space-y-2">
          {incidents.map((incident) => (
            <Link
              key={incident.id}
              href={`/incidents/${incident.id}`}
              className="flex items-center justify-between rounded-xl border border-border px-4 py-3 transition-colors hover:bg-muted/50"
            >
              <div>
                <p className="text-sm font-medium">{incident.title}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {new Date(incident.created_at).toLocaleString()}
                </p>
              </div>
              <StatusBadge status={incident.status} />
            </Link>
          ))}
        </div>
      )}

      {showModal && (
        <TriggerModal
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            void refreshIncidents();
          }}
        />
      )}
    </main>
  );
}
