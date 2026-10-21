import { useCallback, useEffect, useState } from "react";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import { errorMessage } from "../types/threatIntelligence";

export default function useIndicators(filters) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const refresh = useCallback(() => setReload((value) => value + 1), []);
  useEffect(() => {
    let live = true;
    setLoading(true);
    threatIntelligenceService
      .indicators(filters)
      .then((value) => {
        if (live) {
          setData(value);
          setError("");
        }
      })
      .catch((cause) => {
        if (live) {
          setData(null);
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
  return { data, loading, error, refresh };
}
