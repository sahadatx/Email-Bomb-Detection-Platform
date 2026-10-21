import { useEffect, useMemo, useState } from "react";
import { DEFAULT_ANALYTICS_FILTERS } from "../types";

export function useAnalyticsFilters() {
  const [filters, setFilters] = useState(DEFAULT_ANALYTICS_FILTERS);
  const [debounced, setDebounced] = useState(filters);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(filters), 250);
    return () => window.clearTimeout(timer);
  }, [filters]);
  const requestFilters = useMemo(() => {
    if (debounced.time_range === "custom" && (!debounced.from_date || !debounced.to_date)) return null;
    return {
      ...debounced,
      from_date: debounced.time_range === "custom" ? `${debounced.from_date}T00:00:00Z` : undefined,
      to_date: debounced.time_range === "custom" ? `${debounced.to_date}T23:59:59Z` : undefined,
    };
  }, [debounced]);
  const update = (key, value) => setFilters((current) => ({ ...current, [key]: value }));
  const reset = () => setFilters(DEFAULT_ANALYTICS_FILTERS);
  return { filters, requestFilters, update, reset };
}
