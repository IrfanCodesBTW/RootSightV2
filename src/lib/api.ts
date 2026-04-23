import type {
  Incident,
  TriggerPipelineRequest,
  TriggerPipelineResponse,
  ListIncidentsResponse,
  ApiResponse,
} from "@/types";
import { generateMockIncident } from "./mock-data";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Helpers ─────────────────────────────────────────────────────────────────────

async function fetchJson<T>(
  url: string,
  init?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
    const body = await res.json();
    if (!res.ok || body?.success === false) {
      return {
        success: false,
        data: null,
        error:
          body?.error ?? body?.message ?? `HTTP ${res.status}: ${res.statusText}`,
      };
    }
    // API returns { success, data, error } envelope
    if ("data" in body) {
      return { success: true, data: body.data as T, error: null };
    }
    return { success: true, data: body as T, error: null };
  } catch (e) {
    const message = e instanceof Error ? e.message : "Network error";
    return { success: false, data: null, error: message };
  }
}

// ── Demo mode helpers ───────────────────────────────────────────────────────────

const DEMO_MODE =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_DEMO_MODE === "true"
    : false;

function isDemoMode(): boolean {
  return DEMO_MODE;
}

// ── API Client ──────────────────────────────────────────────────────────────────

class RootSightAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  /** Check if backend is healthy */
  async checkBackendHealth(): Promise<{ healthy: boolean }> {
    try {
      const res = await fetchJson<{ status: string; version: string }>(
        `${this.baseUrl}/api/health`
      );
      return { healthy: res.success && res.data?.status === "ok" };
    } catch {
      return { healthy: false };
    }
  }

  /** Trigger the analysis pipeline */
  async triggerPipeline(
    req: TriggerPipelineRequest
  ): Promise<TriggerPipelineResponse> {
    if (isDemoMode()) {
      const mockId = `demo-${Date.now().toString(36)}`;
      return { incident_id: mockId, status: "pipeline_started" };
    }

    const payload: Record<string, unknown> = {};
    if (req.title) payload.title = req.title;
    if (req.severity) payload.severity = req.severity;
    if (req.source) payload.source = req.source;
    if (req.bundle_file) payload.bundle_file = req.bundle_file;
    if (req.payload) {
      try {
        const parsed = JSON.parse(req.payload);
        Object.assign(payload, parsed);
      } catch {
        // If payload is not valid JSON, use it as description
        payload.description = req.payload;
      }
    }

    const res = await fetchJson<TriggerPipelineResponse>(
      `${this.baseUrl}/api/trigger`,
      { method: "POST", body: JSON.stringify(payload) }
    );

    if (!res.success || !res.data) {
      throw new Error(res.error ?? "Failed to trigger pipeline");
    }
    return res.data;
  }

  /** Get a single incident by ID */
  async getIncident(incidentId: string): Promise<Incident | null> {
    if (isDemoMode()) {
      return generateMockIncident(incidentId);
    }

    const res = await fetchJson<Incident>(
      `${this.baseUrl}/api/incidents/${incidentId}`
    );
    return res.data ?? null;
  }

  /** List all incidents */
  async listIncidents(
    page: number = 1,
    limit: number = 20
  ): Promise<ListIncidentsResponse> {
    const emptyResponse: ListIncidentsResponse = {
      items: [],
      total: 0,
      page,
      limit,
    };

    if (isDemoMode()) {
      const items = [
        generateMockIncident("demo-1"),
        generateMockIncident("demo-2"),
        generateMockIncident("demo-3"),
      ];
      return { items, total: items.length, page: 1, limit: 20 };
    }

    const res = await fetchJson<ListIncidentsResponse>(
      `${this.baseUrl}/api/incidents?page=${page}&limit=${limit}`
    );
    return res.data ?? emptyResponse;
  }

  /** Get pipeline state for an incident */
  async getPipelineState(
    incidentId: string
  ): Promise<ApiResponse<Incident>> {
    if (isDemoMode()) {
      return {
        success: true,
        data: generateMockIncident(incidentId),
        error: null,
      };
    }

    return fetchJson<Incident>(
      `${this.baseUrl}/api/incidents/${incidentId}/pipeline`
    );
  }

  /** Draft a recovery script */
  async draftRecoveryScript(
    incidentId: string
  ): Promise<{ script: string } | null> {
    const res = await fetchJson<{ script: string }>(
      `${this.baseUrl}/api/incident/${incidentId}/draft-script`,
      { method: "POST" }
    );
    return res.data ?? null;
  }
}

// ── Singleton export ────────────────────────────────────────────────────────────
export const api = new RootSightAPI();
export { RootSightAPI };
