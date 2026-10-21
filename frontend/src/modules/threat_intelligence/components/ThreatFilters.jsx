import { RotateCcw } from "lucide-react";
import {
  FEED_TYPES,
  INDICATOR_TYPES,
  MATCH_STATUSES,
  THREAT_SEVERITIES,
  displayLabel,
} from "../types/threatIntelligence";

export default function ThreatFilters({
  fields,
  values,
  onChange,
  onReset,
  children,
  className = "",
}) {
  return (
    <section className={`ti-filters ${className}`.trim()} aria-label="Threat filters">
      <div className="ti-filter-grid">
        {fields.map((field) => (
          <label
            key={field.key}
            className={field.key === "search" ? "ti-filter-search" : undefined}
          >
            {field.label}
            {field.type === "search" ? (
              <input
                value={values[field.key] || ""}
                onChange={(event) => onChange(field.key, event.target.value)}
                placeholder={field.placeholder || "Search..."}
              />
            ) : (
              <select
                value={values[field.key] || ""}
                onChange={(event) => onChange(field.key, event.target.value)}
              >
                <option value="">{field.allLabel || "All"}</option>
                {(
                  field.options ||
                  (field.kind === "type"
                    ? INDICATOR_TYPES
                    : field.kind === "feed_type"
                      ? FEED_TYPES
                      : field.kind === "status"
                        ? MATCH_STATUSES
                        : field.kind === "severity"
                          ? THREAT_SEVERITIES
                          : [])
                ).map((option) => {
                  const value =
                    typeof option === "string" ? option : option.value;
                  const label =
                    typeof option === "string"
                      ? displayLabel(option)
                      : option.label;
                  return (
                    <option value={value} key={value}>
                      {label}
                    </option>
                  );
                })}
              </select>
            )}
          </label>
        ))}
        {children}
      </div>
      <div className="ti-filter-footer">
        <span>Filters refresh results automatically.</span>
        <button
          type="button"
          className="ti-button ti-button--quiet"
          onClick={onReset}
        >
          <RotateCcw size={15} /> Reset Filters
        </button>
      </div>
    </section>
  );
}
