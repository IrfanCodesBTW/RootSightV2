import ConfidenceBar from "@/components/shared/ConfidenceBar";
import type { Hypothesis } from "@/types";

interface RCAPanelProps {
  hypotheses: Hypothesis[];
}

export function RCAPanel({ hypotheses }: RCAPanelProps) {
  if (!hypotheses || hypotheses.length === 0) {
    return (
      <section className="rounded-xl border border-border p-4">
        <p className="text-sm font-medium">Root Cause Analysis</p>
        <p className="mt-2 text-sm text-muted-foreground">No hypotheses yet.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4 rounded-xl border border-border p-4">
      <p className="text-sm font-medium">Root Cause Analysis</p>
      {hypotheses.map((hypothesis) => (
        <article key={`${hypothesis.rank}-${hypothesis.hypothesis_id}`} className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium">
              #{hypothesis.rank} {hypothesis.statement}
            </p>
            <div className="w-36">
              <ConfidenceBar confidence={hypothesis.confidence_score} />
            </div>
          </div>
          {hypothesis.severity_band && (
            <p className="text-xs text-yellow-500">
              Severity override: {hypothesis.severity_band}
            </p>
          )}
          {hypothesis.supporting_evidence && hypothesis.supporting_evidence.length > 0 && (
            <ul className="list-inside list-disc text-xs text-muted-foreground">
              {hypothesis.supporting_evidence.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </article>
      ))}
    </section>
  );
}
