import type { SimilarIncident } from "@/types";

interface MemoryCardProps {
  similarIncidents: SimilarIncident[];
}

export function MemoryCard({ similarIncidents }: MemoryCardProps) {
  if (!similarIncidents || similarIncidents.length === 0) {
    return (
      <section className="rounded-xl border border-border p-4">
        <p className="text-sm font-medium">Similar Past Incidents</p>
        <p className="mt-2 text-sm text-muted-foreground">No similar incidents found.</p>
      </section>
    );
  }

  return (
    <section className="space-y-3 rounded-xl border border-border p-4">
      <p className="text-sm font-medium">Similar Past Incidents</p>

      {similarIncidents.map((incident) => (
        <article key={`${incident.incident_id}-${incident.similar_to_id}`} className="space-y-1">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium">{incident.why_similar}</p>
            <span className="text-xs text-muted-foreground">
              {Math.round(incident.similarity_score * 100)}% match
            </span>
          </div>
          <p className="text-xs text-muted-foreground">Fix: {incident.previous_fix}</p>
        </article>
      ))}
    </section>
  );
}
