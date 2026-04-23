import { useState, useCallback, useRef, useEffect } from "react";

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timeoutIds = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // Cleanup all timeouts on unmount
  useEffect(() => {
    const currentTimeouts = timeoutIds.current;
    return () => {
      currentTimeouts.forEach((tid) => clearTimeout(tid));
      currentTimeouts.clear();
    };
  }, []);

  const showToast = useCallback((message: string, type: Toast["type"]) => {
    const id = Date.now().toString();
    const newToast: Toast = { id, message, type };

    setToasts((prev) => {
      const next = [newToast, ...prev];
      if (next.length > 3) {
        // Clean up timeout for removed toast
        const removed = next[3];
        if (removed) {
          const tid = timeoutIds.current.get(removed.id);
          if (tid) {
            clearTimeout(tid);
            timeoutIds.current.delete(removed.id);
          }
        }
        return next.slice(0, 3);
      }
      return next;
    });

    const tid = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
      timeoutIds.current.delete(id);
    }, 3500);

    timeoutIds.current.set(id, tid);
  }, []);

  return { toasts, showToast };
}
