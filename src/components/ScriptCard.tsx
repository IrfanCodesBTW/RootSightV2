"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";

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
      const result = await api.draftRecoveryScript(incidentId);
      if (result) {
        setScript(result.script);
      } else {
        setError("Failed to draft recovery script.");
      }
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Failed to draft recovery script.");
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  if (!incidentId) return null;

  return (
    <section className="space-y-3 rounded-xl border border-white/[0.07] p-4 bg-white/[0.02]">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-200">Recovery Script</p>
        <button
          onClick={() => void handleDraft()}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {loading ? "Drafting..." : "Draft with AI"}
        </button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {script ? (
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-black/40 border border-white/[0.07] p-3 text-[11px] font-mono text-gray-400 leading-relaxed">
          {script}
        </pre>
      ) : (
        <p className="text-xs text-gray-500 italic">Generate a draft script when RCA is ready.</p>
      )}
    </section>
  );
}
