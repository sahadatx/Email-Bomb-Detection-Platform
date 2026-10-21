import { useCallback, useEffect, useState } from "react";
import { experimentsService } from "../services/experimentsService";
import { errorText } from "../types";

/** Server-paginated experiment query state. Filters are sent directly to the API. */
export default function useExperiments(params) {
  const [result, setResult] = useState({ items: [], total: 0, total_pages: 1, summary: null });
  const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [reload, setReload] = useState(0);
  const refresh = useCallback(() => setReload((value) => value + 1), []);
  useEffect(() => { let current = true; setLoading(true); experimentsService.list(params).then((value) => { if (current) { setResult(value); setError(""); } }).catch((cause) => { if (current) { setError(errorText(cause)); setResult({ items: [], total: 0, total_pages: 1, summary: null }); } }).finally(() => { if (current) setLoading(false); }); return () => { current = false; }; }, [params, reload]);
  return { ...result, loading, error, refresh };
}
