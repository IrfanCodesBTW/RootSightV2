"use client";

import { useCallback } from "react";
import { useLayout } from "@/app/layout-client";
import type { Action } from "@/types/incident";

interface ActionsCardProps {
  actions: Action[];
  incidentId: string;
}

export function ActionsCard({ actions, incidentId }: ActionsCardProps) {
  const { showToast } = useLayout();

  const handleCopy = useCallback(
    async (content: string) => {
      try {
        await navigator.clipboard.writeText(content);
        showToast("Copied", "success");
      } catch {
        showToast("Failed to copy", "error");
      }
    },
    [showToast]
  );

  if (!incidentId) return null;
  if (!actions || actions.length === 0) {
    return (
      <section className="rounded-xl border border-border p-4">
        <p className="text-sm font-medium">Actions</p>
        <p className="mt-2 text-sm text-muted-foreground">No actions generated yet.</p>
      </section>
    );
  }

  return (
    <section className="space-y-3 rounded-xl border border-border p-4">
      <p className="text-sm font-medium">Actions</p>
      {actions.map((action) => (
        <article key={action.id} className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium">{action.title}</p>
            <button
              onClick={() => void handleCopy(action.content)}
              className="text-xs text-muted-foreground underline hover:text-foreground"
            >
              Copy
            </button>
          </div>
          <pre className="max-h-44 overflow-auto whitespace-pre-wrap rounded bg-muted p-2 text-xs">
            {action.content}
          </pre>
        </article>
      ))}
    </section>
  );
}
