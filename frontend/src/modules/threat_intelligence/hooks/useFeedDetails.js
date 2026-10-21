import { useCallback, useEffect, useState } from "react";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import { errorMessage } from "../types/threatIntelligence";

export default function useFeedDetails(feedId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    if (!feedId) return;
    setLoading(true);
    try {
      setData(await threatIntelligenceService.feed(feedId));
      setError("");
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [feedId]);
  useEffect(() => {
    if (feedId) refresh();
    else {
      setData(null);
      setError("");
    }
  }, [feedId, refresh]);
  return { data, setData, loading, error, refresh };
}
