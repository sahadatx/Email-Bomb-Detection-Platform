import { useCallback, useEffect, useState } from "react";
import { experimentsService } from "../services/experimentsService";
import { errorText } from "../types";

export default function useExperimentRuns(experimentId) {
  const [runs, setRuns] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const refresh = useCallback(async () => { setLoading(true); try { setRuns(await experimentsService.runs(experimentId)); setError(""); } catch (cause) { setError(errorText(cause)); } finally { setLoading(false); } }, [experimentId]);
  useEffect(() => { if (experimentId) refresh(); }, [experimentId, refresh]);
  useEffect(() => { if (!runs.some((run) => ["queued", "running"].includes(run.status))) return undefined; const timer = window.setInterval(refresh, 3000); return () => window.clearInterval(timer); }, [runs, refresh]);
  return { runs, loading, error, refresh };
}
