import type { Event } from "@/types";

interface TimelinePanelProps {
  events: Event[];
}

export function TimelinePanel({ events }: TimelinePanelProps) {
  if (!events || events.length === 0) {
    return (
      <section className="rounded-xl border border-border p-4">
        <p className="text-sm font-medium">Timeline</p>
        <p className="mt-2 text-sm text-muted-foreground">Timeline reconstruction pending.</p>
      </section>
    );
  }

  return (
    <section className="space-y-3 rounded-xl border border-border p-4">
      <p className="text-sm font-medium">Timeline</p>
      <ol className="space-y-3">
        {events.map((event) => (
          <li key={event.event_id} className="grid grid-cols-[96px_1fr] gap-3 text-sm">
            <div className="text-xs text-muted-foreground">
              {new Date(event.timestamp).toLocaleTimeString()}
            </div>
            <div className="space-y-1">
              <p>{event.description}</p>
              <p className="text-xs text-muted-foreground">
                {event.event_type}{event.evidence_source ? ` from ${event.evidence_source}` : ""}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
