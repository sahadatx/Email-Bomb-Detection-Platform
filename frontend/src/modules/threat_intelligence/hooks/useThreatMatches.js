import { useCallback, useEffect, useState } from "react";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import { errorMessage } from "../types/threatIntelligence";

export default function useThreatMatches(filters) {
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const refresh = useCallback(() => setReload((value) => value + 1), []);
  useEffect(() => {
    let live = true;
    setLoading(true);
    Promise.all([
      threatIntelligenceService.matches(filters),
      threatIntelligenceService.matchSummary(filters),
    ])
      .then(([matches, overview]) => {
        if (live) {
          setData(matches);
          setSummary(overview);
          setError("");
        }
      })
      .catch((cause) => {
        if (live) {
          setData(null);
          setSummary(null);
          setError(errorMessage(cause));
        }
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [filters, reload]);
  return { data, summary, loading, error, refresh };
}
