"use client";

import { useCallback, useState } from "react";
import { draftRecoveryScript } from "@/lib/api";

interface ScriptCardProps {
  incidentId: string;
}

export function ScriptCard({ incidentId }: ScriptCardProps) {
  const [script, setScript] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDraft = useCallback(async () => {
    if (!incidentId) return;

    setLoading(true);
    setError(null);
    try {
      const result = await draftRecoveryScript(incidentId);
      setScript(result.script);
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Failed to draft recovery script.");
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  if (!incidentId) return null;

  return (
    <section className="space-y-3 rounded-xl border border-border p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">Recovery Script</p>
        <button
          onClick={() => void handleDraft()}
          disabled={loading}
          className="rounded-md bg-primary px-3 py-1 text-xs text-primary-foreground disabled:opacity-50"
        >
          {loading ? "Drafting..." : "Draft with Groq"}
        </button>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {script ? (
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded bg-muted p-3 text-xs">
          {script}
        </pre>
      ) : (
        <p className="text-xs text-muted-foreground">Generate a draft script when RCA is ready.</p>
      )}
    </section>
  );
}
