import type { Impact } from "@/types";

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
          <p className="font-medium capitalize">{impact.severity_band ?? "Unknown"}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Estimated users</p>
          <p className="font-medium">
            {impact.affected_users != null ? impact.affected_users.toLocaleString() : "N/A"}
          </p>
        </div>
        <div className="md:col-span-2">
          <p className="text-xs text-muted-foreground">Affected services</p>
          <p>{impact.affected_services?.join(", ") || "None reported"}</p>
        </div>
        <div className="md:col-span-2">
          <p className="text-xs text-muted-foreground">User impact</p>
          <p>{impact.probable_user_impact ?? "Impact assessment pending"}</p>
        </div>
        <div className="md:col-span-2">
          <p className="text-xs text-muted-foreground">Business impact</p>
          <p>{impact.business_impact_summary ?? "Not yet assessed"}</p>
        </div>
      </div>
    </section>
  );
}
