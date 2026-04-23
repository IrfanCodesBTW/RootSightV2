"use client";

import { cn, confidenceColor, confidenceBgColor } from "@/lib/utils";

interface ConfidenceBarProps {
  value: number; // 0.0 – 1.0
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function ConfidenceBar({
  value,
  size = "md",
  showLabel,
}: ConfidenceBarProps) {
  // Logic: default true for md/lg, false for sm
  const shouldShowLabel = showLabel ?? (size !== "sm");

  const heightClass = {
    sm: "h-1",
    md: "h-1.5",
    lg: "h-2.5",
  }[size];

  const percentage = Math.round(value * 100);

  return (
    <div className="flex items-center gap-2 w-full">
      <div className={cn("flex-1 bg-white/10 rounded-full overflow-hidden", heightClass)}>
        <div
          className={cn(
            "h-full transition-all duration-700 ease-out rounded-full",
            confidenceBgColor(value)
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {shouldShowLabel && (
        <div className={cn("w-8 text-right text-xs font-mono font-bold", confidenceColor(value))}>
          {percentage}%
        </div>
      )}
    </div>
  );
}
