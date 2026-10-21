import { useEffect } from "react";

export default function useDashboardRefresh(refresh, intervalMs = 60000) {
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") refresh();
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [refresh, intervalMs]);
}
