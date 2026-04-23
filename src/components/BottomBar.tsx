"use client";

import { useCallback } from "react";
import type { Incident } from "@/types";

interface BottomBarProps {
  incident: Incident;
}

export function BottomBar({ incident }: BottomBarProps) {
  const handleExport = useCallback(() => {
    const blob = new Blob([JSON.stringify(incident, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `rootsight-${incident.incident_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [incident]);

  if (!incident) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between border-t border-border bg-background/90 px-6 py-3 backdrop-blur-sm">
      <p className="text-xs text-muted-foreground">
        {incident.incident?.title ?? "Untitled"} - {incident.status}
      </p>
      <button
        onClick={handleExport}
        className="rounded-md border border-border px-3 py-1.5 text-xs transition-colors hover:bg-muted"
      >
        Export JSON
      </button>
    </div>
  );
}
