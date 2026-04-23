import { cn } from "@/lib/utils";
import { Incident, PipelineState, PipelineStepStatus, IncidentStatus } from "@/types";
import { PIPELINE_STEPS } from "@/types";

interface PipelineTrackerProps {
  incident: Incident;
}

export function PipelineTracker({ incident }: PipelineTrackerProps) {
  if (!incident) return null;

  const pipelineState = incident.pipeline_steps;
  if (!pipelineState) {
    return (
      <section className="space-y-3 rounded-xl border border-border p-4">
        <p className="text-sm font-medium">Pipeline Progress</p>
        <p className="text-sm text-muted-foreground">Pipeline not started yet.</p>
      </section>
    );
  }

  const pipelineKeys = Object.keys(pipelineState) as Array<keyof PipelineState>;
  const completedSteps = pipelineKeys.filter(
    (k) => pipelineState[k]?.status === PipelineStepStatus.COMPLETE
  ).length;
  const progress = pipelineKeys.length > 0
    ? Math.round((completedSteps / pipelineKeys.length) * 100)
    : 0;

  return (
    <section className="space-y-3 rounded-xl border border-border p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">Pipeline Progress</p>
        <p className="text-xs text-muted-foreground">{progress}%</p>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {PIPELINE_STEPS.map((step) => {
          const stepState = pipelineState[step.key];
          const status: PipelineStepStatus = stepState?.status ?? PipelineStepStatus.PENDING;
          const done = status === PipelineStepStatus.COMPLETE;
          const active = status === PipelineStepStatus.RUNNING;
          const failed = status === PipelineStepStatus.FAILED;

          return (
            <span
              key={step.key}
              className={cn(
                "rounded-full border px-2 py-0.5 text-xs capitalize",
                done && "border-green-300 bg-green-100 text-green-700",
                active && "border-primary bg-primary text-primary-foreground",
                failed && "border-red-300 bg-red-100 text-red-700",
                !done && !active && !failed && "border-border text-muted-foreground"
              )}
            >
              {step.label}
            </span>
          );
        })}
      </div>

      {incident.status === IncidentStatus.FAILED && (
        <p className="text-xs text-destructive">
          Pipeline failed. Check logs for details.
        </p>
      )}
      {incident.status === IncidentStatus.DEGRADED && (
        <p className="text-xs text-yellow-500">
          Pipeline ran in degraded mode — some data sources were unavailable.
        </p>
      )}
    </section>
  );
}
