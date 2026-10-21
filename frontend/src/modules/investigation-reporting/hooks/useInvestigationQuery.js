import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

export default function useInvestigationQuery(defaultFilters, pageSize = 30) {
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState(() => Math.max(1, Number(params.get("page")) || 1));
  const [search, setSearchValue] = useState(() => params.get("search") || "");
  const [filters, setFilters] = useState(() => Object.fromEntries(Object.keys(defaultFilters).map((key) => [key, params.get(key) || defaultFilters[key]])));
  const activeFilterCount = useMemo(() => Object.values(filters).filter(Boolean).length, [filters]);
  useEffect(() => {
    // Keep page-specific parameters such as `edit` and deep-link IDs while
    // syncing the shared list state into the URL.
    const known = new Set(["search", "page", ...Object.keys(defaultFilters)]);
    const next = new URLSearchParams();
    params.forEach((value, key) => { if (!known.has(key)) next.append(key, value); });
    if (search.trim()) next.set("search", search.trim());
    if (page > 1) next.set("page", String(page));
    Object.entries(filters).forEach(([key, value]) => { if (value !== "" && value != null) next.set(key, String(value)); });
    if (next.toString() !== params.toString()) setParams(next, { replace: true });
  }, [search, page, filters, params, setParams, defaultFilters]);
  const setSearch = (value) => { setSearchValue(value); setPage(1); };
  const reset = () => { setSearchValue(""); setFilters(defaultFilters); setPage(1); };
  return { page, setPage, pageSize, search, setSearch, filters, setFilters, reset, activeFilterCount };
}
