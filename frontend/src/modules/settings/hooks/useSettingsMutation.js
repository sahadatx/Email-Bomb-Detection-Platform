import { useState } from "react";
import { settingsApi } from "../services/settingsApi";

export default function useSettingsMutation() {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [savedAt, setSavedAt] = useState(null);

  async function save(category, values, reason) {
    setSaving(true);
    setError("");
    setSavedAt(null);
    try {
      const result = await settingsApi.updateCategory(category, values, reason);
      setSavedAt(result.saved_at);
      return result;
    } catch (cause) {
      setError(cause.message || "Settings could not be saved.");
      throw cause;
    } finally {
      setSaving(false);
    }
  }

  return { save, saving, error, setError, savedAt };
}
