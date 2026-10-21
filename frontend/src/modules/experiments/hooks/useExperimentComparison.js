import { useCallback, useState } from "react";
import { experimentsService } from "../services/experimentsService";
import { errorText } from "../types";

export default function useExperimentComparison() {
  const [items, setItems] = useState([]); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const compare = useCallback(async (experimentIds) => { if (experimentIds.length < 2) return []; setLoading(true); setError(""); try { const result = await experimentsService.compare(experimentIds); setItems(result.items || []); return result.items || []; } catch (cause) { setError(errorText(cause)); setItems([]); return []; } finally { setLoading(false); } }, []);
  const clear = useCallback(() => { setItems([]); setError(""); }, []);
  return { items, loading, error, compare, clear };
}
