import { useCallback, useEffect, useState } from "react";
import { analyticsService } from "../services/analyticsService";

const EMPTY = { overview: null, classification: null, risk: null, performance: null, behavior: null, recent: [] };

export function useAnalytics(filters) {
  const [data, setData] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const refresh = useCallback(() => setReloadKey((value) => value + 1), []);
  useEffect(() => {
    if (!filters) { setLoading(false); return undefined; }
    let active = true;
    setLoading(true); setError("");
    Promise.all([
      analyticsService.overview(filters), analyticsService.classification(filters), analyticsService.risk(filters),
      analyticsService.performance({ ...filters, evaluation_split: "validation" }), analyticsService.behavior(filters), analyticsService.recent(filters),
    ]).then(([overview, classification, risk, performance, behavior, recent]) => {
      if (active) setData({ overview, classification, risk, performance, behavior, recent: recent.items || [] });
    }).catch((cause) => { if (active) { setError(cause?.message || "Could not load analytics data."); setData(EMPTY); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filters, reloadKey]);
  return { data, loading, error, refresh };
}
