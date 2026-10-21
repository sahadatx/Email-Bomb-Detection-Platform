import { useCallback, useEffect, useState } from "react";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import { errorMessage } from "../types/threatIntelligence";

export default function useIndicatorDetails(indicatorId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    if (!indicatorId) return;
    setLoading(true);
    try {
      setData(await threatIntelligenceService.indicator(indicatorId));
      setError("");
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [indicatorId]);
  useEffect(() => {
    if (indicatorId) refresh();
    else {
      setData(null);
      setError("");
    }
  }, [indicatorId, refresh]);
  return { data, setData, loading, error, refresh };
}
