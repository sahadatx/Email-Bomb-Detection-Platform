import { useCallback, useEffect, useState } from "react";
import { experimentsService } from "../services/experimentsService";
import { errorText } from "../types";

export default function useExperimentDetails(experimentId) {
  const [experiment, setExperiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    setLoading(true);
    try { setExperiment(await experimentsService.detail(experimentId)); setError(""); }
    catch (cause) { setError(errorText(cause)); }
    finally { setLoading(false); }
  }, [experimentId]);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (!experiment || !["queued", "running"].includes(experiment.status)) return undefined;
    const timer = window.setInterval(async () => { try { setExperiment(await experimentsService.detail(experimentId)); } catch { /* retain last successful state */ } }, 3000);
    return () => window.clearInterval(timer);
  }, [experiment?.status, experimentId]);
  return { experiment, setExperiment, loading, error, refresh };
}
