import { IncidentStatus } from "@/types";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: IncidentStatus;
}

const STATUS_STYLES: Record<IncidentStatus, { label: string; classes: string }> = {
  [IncidentStatus.PENDING]: {
    label: "Pending",
    classes: "border-slate-500/30 bg-slate-500/10 text-slate-400",
  },
  [IncidentStatus.RUNNING]: {
    label: "Running",
    classes: "border-blue-500/30 bg-blue-500/10 text-blue-400 animate-pulse",
  },
  [IncidentStatus.COMPLETED]: {
    label: "Completed",
    classes: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  },
  [IncidentStatus.DEGRADED]: {
    label: "Degraded",
    classes: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  },
  [IncidentStatus.FAILED]: {
    label: "Failed",
    classes: "border-red-500/30 bg-red-500/10 text-red-400",
  },

  [IncidentStatus.PARTIAL]: {
    label: "Partial",
    classes: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] || {
    label: status,
    classes: "border-gray-500/30 bg-gray-500/10 text-gray-400",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider",
        style.classes
      )}
    >
      {style.label}
    </span>
  );
}
