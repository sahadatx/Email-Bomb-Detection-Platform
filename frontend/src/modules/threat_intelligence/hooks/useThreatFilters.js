import { useMemo, useState } from "react";

export default function useThreatFilters(defaults) {
  const [filters, setFilters] = useState(defaults);
  const update = (key, value) =>
    setFilters((previous) => ({
      ...previous,
      [key]: value,
      page: key === "page" ? value : 1,
    }));
  const reset = () => setFilters(defaults);
  const query = useMemo(() => ({ ...filters }), [filters]);
  return { filters, query, update, reset };
}
