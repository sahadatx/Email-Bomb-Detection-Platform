import { useEffect, useState } from "react";
import { settingsApi } from "../services/settingsApi";

export default function useSettings(category) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    settingsApi.getCategory(category, { signal: controller.signal })
      .then(setData)
      .catch((cause) => {
        if (!controller.signal.aborted) setError(cause.message || "Settings could not be loaded.");
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [category, reloadKey]);

  return { data, loading, error, reload: () => setReloadKey((value) => value + 1) };
}
