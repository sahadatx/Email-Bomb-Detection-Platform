import { useCallback, useEffect, useState } from "react";
import { dashboardApi } from "../services/dashboardApi";

export default function useDashboard(filters, ready) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const refresh = useCallback(() => setRefreshKey((value) => value + 1), []);

  useEffect(() => {
    if (!ready) {
      setData(null);
      setError("");
      setLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    dashboardApi
      .getOverview(filters, { signal: controller.signal })
      .then((result) => setData(result))
      .catch((reason) => {
        if (reason.name !== "AbortError")
          setError(reason.message || "Dashboard data could not be loaded.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters, ready, refreshKey]);

  return { data, loading, error, refresh };
}
