import { useCallback, useMemo, useState } from "react";
import { DEFAULT_FILTERS } from "../utils/dashboardConstants";

export default function useDashboardFilters() {
  const [filters, setFilters] = useState(() => ({ ...DEFAULT_FILTERS }));
  const updateFilter = useCallback((name, value) => {
    setFilters((current) => ({ ...current, [name]: value }));
  }, []);
  const resetFilters = useCallback(
    () => setFilters({ ...DEFAULT_FILTERS }),
    [],
  );
  const ready =
    filters.time_range !== "custom" ||
    Boolean(filters.start_date && filters.end_date);
  const queryFilters = useMemo(() => {
    const result = { ...filters };
    if (result.time_range !== "custom") {
      delete result.start_date;
      delete result.end_date;
    }
    Object.keys(result).forEach((key) => {
      if (!result[key]) delete result[key];
    });
    return result;
  }, [filters]);
  return { filters, queryFilters, updateFilter, resetFilters, ready };
}
