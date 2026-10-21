import { useCallback, useEffect, useState } from "react";
import { detectionService } from "../../detection/services/detectionService";
import { evidenceService } from "../services/evidenceService";
import { investigationError } from "../types";

export default function useEvidence({ page, pageSize, search, filters }) {
  const [data, setData] = useState({ items: [], total: 0, summary: {}, page: 1, page_size: pageSize, total_pages: 1 });
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setData(await evidenceService.list({ page, page_size: pageSize, search: search.trim(), ...filters })); }
    catch (cause) { setError(investigationError(cause)); }
    finally { setLoading(false); }
  }, [page, pageSize, search, filters]);
  useEffect(() => { const timer = window.setTimeout(load, 220); return () => window.clearTimeout(timer); }, [load]);
  useEffect(() => { let active = true; detectionService.list({ page: 1, page_size: 100 }).then((result) => { if (active) setDetections(result.items || []); }).catch(() => { if (active) setDetections([]); }); return () => { active = false; }; }, []);
  return { ...data, detections, loading, error, refresh: load };
}
