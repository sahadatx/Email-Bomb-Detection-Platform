import { useEffect, useRef, useState } from "react";
import {
  INDICATOR_TYPES,
  THREAT_SEVERITIES,
} from "../types/threatIntelligence";

export default function IndicatorForm({
  initial,
  onSubmit,
  busy,
  error,
  onDirtyChange,
}) {
  const baseline = useRef(null);
  const [form, setForm] = useState({
    value: "",
    indicator_type: "domain",
    severity: "medium",
    confidence: "",
    source: "manual",
    description: "",
    expires_at: "",
  });
  useEffect(() => {
    const next = initial
      ? {
          value: initial.value,
          indicator_type: initial.indicator_type,
          severity: initial.severity,
          confidence: initial.confidence ?? "",
          source: initial.source,
          description: initial.description || "",
          expires_at: initial.expires_at?.slice(0, 10) || "",
        }
      : {
          value: "",
          indicator_type: "domain",
          severity: "medium",
          confidence: "",
          source: "manual",
          description: "",
          expires_at: "",
        };
    baseline.current = next;
    setForm(next);
    onDirtyChange?.(false);
  }, [initial?.id]);
  const change = (key, value) =>
    setForm((current) => {
      const next = { ...current, [key]: value };
      onDirtyChange?.(
        JSON.stringify(next) !== JSON.stringify(baseline.current),
      );
      return next;
    });
  function submit(event) {
    event.preventDefault();
    onSubmit({
      ...form,
      confidence: form.confidence === "" ? null : Number(form.confidence),
      expires_at: form.expires_at
        ? new Date(`${form.expires_at}T23:59:59Z`).toISOString()
        : null,
    });
  }
  return (
    <form id="ti-editor-form" className="ti-form" onSubmit={submit}>
      <label>
        Indicator Value *
        <input
          required
          minLength={3}
          maxLength={2048}
          value={form.value}
          onChange={(event) => change("value", event.target.value)}
          placeholder="example.com"
        />
      </label>
      <label>
        Indicator Type *
        <select
          required
          value={form.indicator_type}
          onChange={(event) => change("indicator_type", event.target.value)}
        >
          {INDICATOR_TYPES.map((value) => (
            <option key={value} value={value}>
              {value.toUpperCase()}
            </option>
          ))}
        </select>
      </label>
      <label>
        Severity
        <select
          value={form.severity}
          onChange={(event) => change("severity", event.target.value)}
        >
          {THREAT_SEVERITIES.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>
      <label>
        Confidence (0–100)
        <input
          type="number"
          min="0"
          max="100"
          value={form.confidence}
          onChange={(event) => change("confidence", event.target.value)}
          placeholder="50"
        />
      </label>
      <label>
        Source
        <select value={form.source} disabled>
          <option value="manual">Manual</option>
          <option value="feed">Feed</option>
        </select>
      </label>
      <label>
        Expiration Date
        <input
          type="date"
          value={form.expires_at}
          onChange={(event) => change("expires_at", event.target.value)}
        />
      </label>
      <label className="ti-form-wide">
        Description
        <textarea
          rows="4"
          maxLength={10000}
          value={form.description}
          onChange={(event) => change("description", event.target.value)}
          placeholder="Add context about this indicator"
        />
      </label>
      {error && (
        <div className="ti-form-error" role="alert">
          {error}
        </div>
      )}
      <span className="ti-sr-only">
        Use the drawer footer to save or cancel.
      </span>
      {busy && <p className="ti-muted">Saving indicator…</p>}
    </form>
  );
}
