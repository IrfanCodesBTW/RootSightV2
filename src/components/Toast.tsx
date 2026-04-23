"use client";

import { Toast as ToastType } from "@/hooks/useToast";
import { cn } from "@/lib/utils";

interface ToastProps {
  toasts: ToastType[];
}

export function Toast({ toasts }: ToastProps) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col-reverse gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "pointer-events-auto bg-[--bg-card] border rounded-lg px-4 py-3 text-sm font-medium min-w-64 max-w-80 shadow-xl animate-slide-up transition-all",
            toast.type === "success" && "border-green-500/50 text-green-400",
            toast.type === "error" && "border-red-500/50 text-red-400",
            toast.type === "info" && "border-[--accent]/50 text-[--accent]"
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-2 h-2 rounded-full",
              toast.type === "success" && "bg-green-500",
              toast.type === "error" && "bg-red-500",
              toast.type === "info" && "bg-[--accent]"
            )} />
            {toast.message}
          </div>
        </div>
      ))}
    </div>
  );
}
