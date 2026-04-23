import { ConfidenceBar } from "@/components/ConfidenceBar";
import type { Hypothesis } from "@/types/incident";

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
        <article key={`${hypothesis.rank}-${hypothesis.title}`} className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium">
              #{hypothesis.rank} {hypothesis.title}
            </p>
            <div className="w-36">
              <ConfidenceBar value={hypothesis.confidence} />
            </div>
          </div>
          <p className="text-sm text-muted-foreground">{hypothesis.description}</p>
          {hypothesis.evidence.length > 0 && (
            <ul className="list-inside list-disc text-xs text-muted-foreground">
              {hypothesis.evidence.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </article>
      ))}
    </section>
  );
}
