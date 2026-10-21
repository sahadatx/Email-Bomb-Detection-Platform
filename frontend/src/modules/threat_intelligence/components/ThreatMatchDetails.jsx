import { displayDate, displayLabel } from "../types/threatIntelligence";
export default function ThreatMatchDetails({ match, onRelated, onStatus }) {
  if (!match) return null;
  return (
    <>
      <dl className="ti-definition-list">
        <dt>Email ID</dt>
        <dd>{match.email_id}</dd>
        <dt>Email / Sender</dt>
        <dd>{match.email_label || "—"}</dd>
        <dt>Severity</dt>
        <dd>{displayLabel(match.severity)}</dd>
        <dt>Matched Indicator</dt>
        <dd className="ti-indicator-value">{match.indicator_value}</dd>
        <dt>Indicator Type</dt>
        <dd>{displayLabel(match.indicator_type)}</dd>
        <dt>Classification</dt>
        <dd>{displayLabel(match.classification || "unknown")}</dd>
        <dt>Match Time</dt>
        <dd>{displayDate(match.matched_at)}</dd>
        <dt>Matched Field</dt>
        <dd>{displayLabel(match.matched_field)}</dd>
        <dt>Feed</dt>
        <dd>{match.feed_name || "Manual indicator"}</dd>
        <dt>Detection ID</dt>
        <dd>{match.detection_id || "No detection linked"}</dd>
        <dt>Match Status</dt>
        <dd>
          {onStatus ? (
            <select
              aria-label="Match status"
              value={match.match_status}
              onChange={(event) => onStatus(event.target.value)}
            >
              {["new", "reviewed", "investigating", "resolved"].map((value) => (
                <option key={value} value={value}>
                  {displayLabel(value)}
                </option>
              ))}
            </select>
          ) : (
            displayLabel(match.match_status)
          )}
        </dd>
      </dl>
      {onRelated && (
        <section className="ti-related">
          <h3>Related Records</h3>
          {[
            ["Email", match.email_id, "email"],
            ["Indicator", match.indicator_id, "indicator"],
            ["Detection", match.detection_id, "detection"],
          ].map(([label, value, kind]) => (
            <button
              disabled={!value}
              key={kind}
              onClick={() => onRelated(kind, value)}
            >
              {label}
              <span>{value || "Unavailable"}</span> →
            </button>
          ))}
        </section>
      )}
    </>
  );
}
