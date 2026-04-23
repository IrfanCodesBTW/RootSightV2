import { cn } from "@/lib/utils";
import type { IncidentDetail } from "@/types/incident";

interface PipelineTrackerProps {
  incident: IncidentDetail;
}

const STAGES = ["ingestion", "timeline", "rca", "impact", "memory", "actions", "complete"] as const;

export function PipelineTracker({ incident }: PipelineTrackerProps) {
  if (!incident) return null;

  const currentStage = incident.pipeline_stage || "ingestion";
  const currentIndex = STAGES.indexOf(currentStage as (typeof STAGES)[number]);
  const safeIndex = currentIndex < 0 ? 0 : currentIndex;
  const progress = Math.max(0, Math.min(100, incident.pipeline_progress ?? 0));

  return (
    <section className="space-y-3 rounded-xl border border-border p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">Pipeline Progress</p>
        <p className="text-xs text-muted-foreground capitalize">{currentStage.replaceAll("_", " ")}</p>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {STAGES.map((stage, index) => {
          const done = index < safeIndex;
          const active = index === safeIndex;

          return (
            <span
              key={stage}
              className={cn(
                "rounded-full border px-2 py-0.5 text-xs capitalize",
                done && "border-green-300 bg-green-100 text-green-700",
                active && "border-primary bg-primary text-primary-foreground",
                !done && !active && "border-border text-muted-foreground"
              )}
            >
              {stage}
            </span>
          );
        })}
      </div>

      {incident.status === "failed" && (
        <p className="text-xs text-destructive">
          Pipeline failed during {currentStage.replaceAll("_", " ")}.
        </p>
      )}
    </section>
  );
}
