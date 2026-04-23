"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { triggerIncident, uploadBundle } from "@/lib/api";
import { cn } from "@/lib/utils";
import { X, Upload, ShieldAlert } from "lucide-react";

interface TriggerModalProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const SEVERITY_OPTIONS = ["critical", "high", "medium", "low"] as const;

export function TriggerModal({ onClose, onSuccess }: TriggerModalProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"manual" | "upload">("manual");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Manual Form State
  const [formData, setFormData] = useState({
    title: "",
    service: "",
    severity: "medium" as "critical" | "high" | "medium" | "low",
    environment: "production",
    logs: "",
  });

  // Upload State
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Escape key handler
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  const handleManualSubmit = async () => {
    if (!formData.title || !formData.service) {
      setError("Incident Name and Service are required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        title: formData.title,
        source: "manual" as const,
        severity: formData.severity,
        raw_payload: {
          service: formData.service,
          environment: formData.environment,
          logs: formData.logs
        }
      };

      const { incident_id } = await triggerIncident(payload);
      onSuccess?.();
      router.push(`/incidents/${incident_id}`);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to trigger incident");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUploadSubmit = async () => {
    if (!file) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const { incident_id } = await uploadBundle(file);
      onSuccess?.();
      router.push(`/incidents/${incident_id}`);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to upload bundle");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div 
        className="bg-[--bg-card] border border-[--border] rounded-xl overflow-hidden shadow-2xl animate-slide-up w-full max-w-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[--border] bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="bg-[--accent-dim] p-2 rounded-lg">
              <ShieldAlert className="w-5 h-5 text-[--accent]" />
            </div>
            <h2 className="font-mono font-bold text-sm tracking-widest uppercase">Mission Control</h2>
          </div>
          <button onClick={onClose} className="text-[--text-muted] hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[--border]">
          <button
            onClick={() => setActiveTab("manual")}
            className={cn(
              "flex-1 py-3 text-xs font-bold uppercase tracking-widest transition-all",
              activeTab === "manual" ? "text-[--accent] border-b-2 border-[--accent] bg-[--accent-dim]" : "text-[--text-muted] hover:bg-white/[0.02]"
            )}
          >
            Manual
          </button>
          <button
            onClick={() => setActiveTab("upload")}
            className={cn(
              "flex-1 py-3 text-xs font-bold uppercase tracking-widest transition-all",
              activeTab === "upload" ? "text-[--accent] border-b-2 border-[--accent] bg-[--accent-dim]" : "text-[--text-muted] hover:bg-white/[0.02]"
            )}
          >
            Upload Bundle
          </button>
        </div>

        <div className="p-6">
          {activeTab === "manual" ? (
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[--text-muted] uppercase tracking-wider">Incident Name</label>
                <input
                  type="text"
                  placeholder="e.g. API Gateway 502 Spike"
                  className="w-full bg-black/40 border border-[--border] rounded-lg px-4 py-2 text-sm focus:border-[--accent] outline-none transition-all"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[--text-muted] uppercase tracking-wider">Service</label>
                <input
                  type="text"
                  placeholder="e.g. api-gateway, auth-service"
                  className="w-full bg-black/40 border border-[--border] rounded-lg px-4 py-2 text-sm focus:border-[--accent] outline-none transition-all"
                  value={formData.service}
                  onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-[--text-muted] uppercase tracking-wider">Severity</label>
                  <div className="flex gap-1">
                    {SEVERITY_OPTIONS.map((sev) => (
                      <button
                        key={sev}
                        type="button"
                        onClick={() => setFormData({ ...formData, severity: sev })}
                        className={cn(
                          "flex-1 py-1.5 rounded border text-[10px] font-bold transition-all",
                          formData.severity === sev 
                            ? (sev === "critical" ? "bg-red-500 border-red-500 text-black" :
                               sev === "high" ? "bg-orange-500 border-orange-500 text-black" :
                               sev === "medium" ? "bg-amber-500 border-amber-500 text-black" :
                               "bg-blue-500 border-blue-500 text-black")
                            : "bg-transparent border-[--border] text-[--text-muted] hover:border-[--text-muted]"
                        )}
                      >
                        {sev}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-[--text-muted] uppercase tracking-wider">Environment</label>
                  <div className="flex gap-1">
                    {["production", "staging", "development"].map((env) => (
                      <button
                        key={env}
                        type="button"
                        onClick={() => setFormData({ ...formData, environment: env })}
                        className={cn(
                          "flex-1 py-1.5 rounded border text-[10px] font-bold transition-all",
                          formData.environment === env
                            ? "bg-white border-white text-black"
                            : "bg-transparent border-[--border] text-[--text-muted] hover:border-[--text-muted]"
                        )}
                      >
                        {env === "production" ? "PROD" : env === "staging" ? "STG" : "DEV"}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[--text-muted] uppercase tracking-wider">Raw Logs (Optional)</label>
                <textarea
                  placeholder="Paste raw log lines here (one per line)..."
                  rows={4}
                  className="w-full bg-black/40 border border-[--border] rounded-lg px-4 py-2 text-sm font-mono focus:border-[--accent] outline-none resize-none transition-all"
                  value={formData.logs}
                  onChange={(e) => setFormData({ ...formData, logs: e.target.value })}
                />
                <p className="text-[10px] text-[--text-dim]">Optional — each line becomes a log entry</p>
              </div>

              <button
                onClick={handleManualSubmit}
                disabled={isSubmitting}
                className="w-full bg-[--accent] text-black font-bold py-3 rounded-lg hover:brightness-110 transition-all disabled:opacity-50"
              >
                {isSubmitting ? "Triggering..." : "Trigger Pipeline →"}
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              <div
                className={cn(
                  "border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center gap-4 transition-all group cursor-pointer",
                  isDragging ? "border-[--accent] bg-[--accent-dim]" : "border-[--border] hover:border-[--text-muted] hover:bg-white/[0.01]"
                )}
                onDragOver={(e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e: React.DragEvent) => {
                  e.preventDefault();
                  setIsDragging(false);
                  const droppedFile = e.dataTransfer.files[0];
                  if (droppedFile) setFile(droppedFile);
                }}
                onClick={() => document.getElementById("fileInput")?.click()}
              >
                <input 
                  id="fileInput"
                  type="file" 
                  className="hidden" 
                  accept=".json,.log,.txt,.zip"
                  onChange={(e) => {
                    const selectedFile = e.target.files?.[0];
                    if (selectedFile) setFile(selectedFile);
                  }}
                />
                <Upload className={cn("w-12 h-12 transition-colors", file ? "text-[--accent]" : "text-[--text-muted] group-hover:text-white")} />
                <div className="text-center">
                  <p className="font-bold text-sm">{file ? file.name : "Drop your log file here"}</p>
                  <p className="text-[10px] text-[--text-muted] mt-1">.json  .log  .txt  .zip accepted</p>
                </div>
                {file && (
                  <p className="text-[10px] font-mono text-[--accent] bg-[--accent-dim] px-2 py-0.5 rounded">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                )}
              </div>

              <button
                onClick={handleUploadSubmit}
                disabled={isSubmitting || !file}
                className="w-full bg-[--accent] text-black font-bold py-3 rounded-lg hover:brightness-110 transition-all disabled:opacity-50"
              >
                {isSubmitting ? "Analyzing..." : "Upload & Analyze →"}
              </button>
            </div>
          )}

          {error && (
            <p className="mt-4 text-center text-xs font-bold text-red-400">{error}</p>
          )}
        </div>
      </div>
    </div>
  );
}
