import { useEffect, useRef, useState } from "react";
import { FEED_TYPES } from "../types/threatIntelligence";

export default function FeedForm({
  initial,
  onSubmit,
  busy,
  error,
  onDirtyChange,
}) {
  const baseline = useRef(null);
  const [form, setForm] = useState({
    name: "",
    feed_type: "csv",
    url: "",
    auth_type: "none",
    credential: "",
    sync_interval_minutes: 60,
    description: "",
    enabled: true,
  });
  useEffect(() => {
    const next = initial
      ? {
          name: initial.name,
          feed_type: initial.feed_type,
          url: initial.url || "",
          auth_type: initial.auth_type,
          credential: "",
          sync_interval_minutes: initial.sync_interval_minutes,
          description: initial.description || "",
          enabled: initial.enabled,
        }
      : {
          name: "",
          feed_type: "csv",
          url: "",
          auth_type: "none",
          credential: "",
          sync_interval_minutes: 60,
          description: "",
          enabled: true,
        };
    baseline.current = next;
    setForm(next);
    onDirtyChange?.(false);
  }, [initial?.id]);
  const change = (key, value) =>
    setForm((current) => {
      const next = { ...current, [key]: value };
      if (key === "feed_type" && value === "internal") {
        next.auth_type = "none";
        next.credential = "";
      }
      onDirtyChange?.(
        JSON.stringify(next) !== JSON.stringify(baseline.current),
      );
      return next;
    });
  function submit(event) {
    event.preventDefault();
    const body = {
      ...form,
      sync_interval_minutes: Number(form.sync_interval_minutes),
    };
    if (!body.credential) delete body.credential;
    onSubmit(body);
  }
  return (
    <form id="ti-editor-form" className="ti-form" onSubmit={submit}>
      <label>
        Feed Name *
        <input
          required
          minLength={2}
          maxLength={180}
          value={form.name}
          onChange={(event) => change("name", event.target.value)}
          placeholder="Community threat feed"
        />
      </label>
      <label>
        Feed Type *
        <select
          value={form.feed_type}
          onChange={(event) => change("feed_type", event.target.value)}
        >
          {FEED_TYPES.map((value) => (
            <option key={value} value={value}>
              {value.toUpperCase().replace("_", " / ")}
            </option>
          ))}
        </select>
      </label>
      {form.feed_type !== "internal" && (
        <label className="ti-form-wide">
          Feed URL *
          <input
            type="url"
            required
            value={form.url}
            onChange={(event) => change("url", event.target.value)}
            placeholder="https://feeds.example.org/iocs.json"
          />
          <small>
            External feeds must use HTTPS and resolve to public IP addresses.
          </small>
        </label>
      )}
      {form.feed_type !== "internal" && (
        <label>
          Authentication
          <select
            value={form.auth_type}
            onChange={(event) => change("auth_type", event.target.value)}
          >
            <option value="none">None</option>
            <option value="api_key">API Key</option>
            <option value="bearer">Bearer Token</option>
            <option value="basic">Basic (username:password)</option>
          </select>
        </label>
      )}
      {form.feed_type !== "internal" && form.auth_type !== "none" && (
        <label>
          Credential{" "}
          {initial?.has_credential ? "(leave blank to keep saved secret)" : "*"}
          <input
            type="password"
            autoComplete="new-password"
            required={!initial?.has_credential}
            value={form.credential}
            onChange={(event) => change("credential", event.target.value)}
            placeholder={
              initial?.has_credential
                ? "Saved securely; enter to replace"
                : "Secret credential"
            }
          />
        </label>
      )}
      <label>
        Sync Interval (minutes)
        <input
          type="number"
          min="5"
          max="10080"
          required
          value={form.sync_interval_minutes}
          onChange={(event) =>
            change("sync_interval_minutes", event.target.value)
          }
        />
      </label>
      <label className="ti-toggle-label">
        <input
          type="checkbox"
          checked={form.enabled}
          onChange={(event) => change("enabled", event.target.checked)}
        />{" "}
        Enable Feed
      </label>
      <label className="ti-form-wide">
        Description
        <textarea
          rows="3"
          maxLength={10000}
          value={form.description}
          onChange={(event) => change("description", event.target.value)}
        />
      </label>
      {error && (
        <div className="ti-form-error" role="alert">
          {error}
        </div>
      )}
      {busy && <p className="ti-muted">Saving feed…</p>}
    </form>
  );
}
