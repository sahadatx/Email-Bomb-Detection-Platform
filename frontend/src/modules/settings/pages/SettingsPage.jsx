import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../../core/auth/AuthProvider";
import { PERMISSIONS, hasPermission } from "../../../core/permissions/permissions";
import ErrorNotice from "../../../core/components/ErrorNotice";
import SettingsErrorState from "../components/SettingsErrorState";
import SettingsHeader from "../components/SettingsHeader";
import SettingsSaveBar from "../components/SettingsSaveBar";
import SettingsSection from "../components/SettingsSection";
import SettingsSidebar from "../components/SettingsSidebar";
import useSettings from "../hooks/useSettings";
import useSettingsMutation from "../hooks/useSettingsMutation";
import { settingsApi } from "../services/settingsApi";
import { CATEGORY_ROUTE, SETTINGS_CATEGORIES } from "../utils/settingsConstants";
import "../styles/settings.css";

export default function SettingsPage() {
  const { category: routeCategory } = useParams();
  const categoryId = SETTINGS_CATEGORIES.some((item) => item.id === routeCategory) ? routeCategory : "general";
  const navigate = useNavigate();
  const { user } = useAuth();
  const canUpdate = hasPermission(user, PERMISSIONS.SYSTEM_SETTINGS_UPDATE);
  const { data, loading, error, reload } = useSettings(categoryId);
  const mutation = useSettingsMutation();
  const [values, setValues] = useState({});
  const [reason, setReason] = useState("");
  const [formError, setFormError] = useState("");
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    const controller = new AbortController();
    settingsApi.getOverview({ signal: controller.signal })
      .then((overview) => setCategories(overview.categories || []))
      .catch(() => { /* The category endpoint remains the source of truth for the active view. */ });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (data) {
      setValues(Object.fromEntries(data.fields.map((field) => [field.key, field.value])));
      setReason("");
      setFormError("");
      mutation.setError("");
    }
  // The category response is the intentional reset point for form state.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  useEffect(() => {
    if (!routeCategory) navigate(CATEGORY_ROUTE("general"), { replace: true });
  }, [routeCategory, navigate]);

  const dirty = useMemo(() => Boolean(data) && data.fields.some((field) => values[field.key] !== field.value), [data, values]);

  useEffect(() => {
    if (!dirty) return undefined;
    const warn = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function guardNavigation(event) {
    const anchor = event.target.closest("a[href]");
    if (!anchor || !dirty) return;
    if (!window.confirm("You have unsaved settings. Discard these changes?")) event.preventDefault();
  }

  function reset() {
    setValues(Object.fromEntries((data?.fields || []).map((field) => [field.key, field.value])));
    setReason("");
    setFormError("");
    mutation.setError("");
  }

  async function save() {
    if (!dirty || !canUpdate) return;
    if (reason.trim().length < 3) {
      setFormError("Enter a change reason with at least three characters.");
      return;
    }
    setFormError("");
    try {
      const result = await mutation.save(categoryId, values, reason);
      setValues(Object.fromEntries(result.category.fields.map((field) => [field.key, field.value])));
      setReason("");
    } catch {
      // The mutation hook keeps the API validation message visible in the form.
    }
  }

  const current = SETTINGS_CATEGORIES.find((item) => item.id === categoryId);

  return <main className="settings-page" onClickCapture={guardNavigation}>
    <SettingsHeader title="System Settings" description="Manage platform configuration with audited, permission-checked changes." connectionState={error ? "unavailable" : loading || !data ? "loading" : "connected"} />
    <div className="settings-layout"><SettingsSidebar categories={categories} /><section className="settings-content">
      {error ? <SettingsErrorState error={error} onRetry={reload} /> : loading ? <div className="settings-loading" aria-busy="true"><i /><i /><i /></div> : data ? <>
        <SettingsSection category={data} values={values} onChange={(key, value) => setValues((currentValues) => ({ ...currentValues, [key]: value }))} disabled={!canUpdate || mutation.saving} />
        {data.editable && !canUpdate && <div className="settings-permission-note">You have read-only access to this configuration.</div>}
        {(formError || mutation.error) && <ErrorNotice className="settings-form-error" title="Settings could not be saved" message={formError || mutation.error} />}
        {data.editable && canUpdate && <SettingsSaveBar dirty={dirty} editable={canUpdate} saving={mutation.saving} reason={reason} onReasonChange={setReason} onReset={reset} onSave={save} savedAt={mutation.savedAt} />}
      </> : <div className="settings-empty">Select a settings category.</div>}
    </section></div>
    {current && <span className="settings-current-category" aria-live="polite">{current.label}</span>}
  </main>;
}
