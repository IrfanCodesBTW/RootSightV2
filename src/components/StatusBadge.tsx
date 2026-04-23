import { cn } from "@/lib/utils";
import type { IncidentStatus } from "@/types/incident";

interface StatusBadgeProps {
  status: IncidentStatus;
}

const STATUS_STYLES: Record<IncidentStatus, { label: string; classes: string }> = {
  pending: {
    label: "Pending",
    classes: "border-slate-300 bg-slate-100 text-slate-700",
  },
  processing: {
    label: "Processing",
    classes: "border-amber-300 bg-amber-100 text-amber-800",
  },
  completed: {
    label: "Completed",
    classes: "border-green-300 bg-green-100 text-green-800",
  },
  failed: {
    label: "Failed",
    classes: "border-red-300 bg-red-100 text-red-800",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const { label, classes } = STATUS_STYLES[status];

  return (
    <span className={cn("inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", classes)}>
      {label}
    </span>
  );
}
