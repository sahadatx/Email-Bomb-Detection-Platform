import { useCallback, useEffect, useState } from "react";
import { explainabilityService } from "../services/explainabilityService";
import { investigationError } from "../types";

export default function useExplainability({ page, pageSize, search, filters }) {
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: pageSize, total_pages: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setData(await explainabilityService.list({ page, page_size: pageSize, search: search.trim(), ...filters })); }
    catch (cause) { setError(investigationError(cause)); }
    finally { setLoading(false); }
  }, [page, pageSize, search, filters]);
  useEffect(() => { const timer = window.setTimeout(load, 220); return () => window.clearTimeout(timer); }, [load]);
  return { ...data, loading, error, refresh: load };
}
