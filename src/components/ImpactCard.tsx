import type { Impact } from "@/types/incident";

interface ImpactCardProps {
  impact: Impact;
}

export function ImpactCard({ impact }: ImpactCardProps) {
  if (!impact) return null;

  return (
    <section className="space-y-3 rounded-xl border border-border p-4">
      <p className="text-sm font-medium">Impact Assessment</p>

      <div className="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
        <div>
          <p className="text-xs text-muted-foreground">Severity</p>
          <p className="font-medium capitalize">{impact.severity_band}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Estimated users</p>
          <p className="font-medium">{impact.estimated_users.toLocaleString()}</p>
        </div>
        <div className="md:col-span-2">
          <p className="text-xs text-muted-foreground">Affected systems</p>
          <p>{impact.affected_systems.join(", ") || "None reported"}</p>
        </div>
        <div className="md:col-span-2">
          <p className="text-xs text-muted-foreground">Business impact</p>
          <p>{impact.business_impact}</p>
        </div>
      </div>
    </section>
  );
}
