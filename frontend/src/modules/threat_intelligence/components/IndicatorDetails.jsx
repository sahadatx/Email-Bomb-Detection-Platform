import { displayDate, displayLabel } from "../types/threatIntelligence";
export default function IndicatorDetails({ item, matches = [], onMatches }) {
  if (!item)
    return <p className="ti-muted">Select an indicator to view details.</p>;
  return (
    <>
      <dl className="ti-definition-list">
        <dt>Indicator</dt>
        <dd className="ti-indicator-value">{item.value}</dd>
        <dt>Type</dt>
        <dd>{displayLabel(item.indicator_type)}</dd>
        <dt>Severity</dt>
        <dd>{displayLabel(item.severity)}</dd>
        <dt>Confidence</dt>
        <dd>{item.confidence == null ? "—" : `${item.confidence}%`}</dd>
        <dt>Status</dt>
        <dd>{displayLabel(item.status)}</dd>
        <dt>Source</dt>
        <dd>{item.feed_name || displayLabel(item.source)}</dd>
        <dt>First Seen</dt>
        <dd>{displayDate(item.first_seen_at)}</dd>
        <dt>Last Seen</dt>
        <dd>{displayDate(item.last_seen_at)}</dd>
        <dt>Created</dt>
        <dd>{displayDate(item.created_at)}</dd>
        <dt>Expires</dt>
        <dd>{displayDate(item.expires_at)}</dd>
        <dt>Description</dt>
        <dd>{item.description || "No description provided."}</dd>
      </dl>
      <section className="ti-related">
        <header>
          <h3>Related Threat Matches</h3>
          <button className="ti-text-button" onClick={onMatches}>
            View matches ({item.matches_count || 0}) →
          </button>
        </header>
        {matches.map((match) => (
          <div key={match.id}>
            {match.email_label || match.email_id} ·{" "}
            {displayDate(match.matched_at)}
          </div>
        ))}
      </section>
    </>
  );
}
