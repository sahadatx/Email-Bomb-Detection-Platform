import { Eye } from "lucide-react";
import { displayDate, displayLabel } from "../types/threatIntelligence";
export default function ThreatMatchTable({ items = [], onView }) {
  return (
    <div className="ti-table-wrap">
      <table className="ti-table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Indicator</th>
            <th>Type</th>
            <th>Classification</th>
            <th>Severity</th>
            <th>Feed</th>
            <th>Match Time</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {items.map((match) => (
            <tr key={match.id} onDoubleClick={() => onView(match)}>
              <td>{match.email_label || match.email_id}</td>
              <td className="ti-indicator-value">{match.indicator_value}</td>
              <td>{displayLabel(match.indicator_type)}</td>
              <td>{displayLabel(match.classification || "unknown")}</td>
              <td>
                <span className={`ti-severity ti-severity--${match.severity}`}>
                  {displayLabel(match.severity)}
                </span>
              </td>
              <td>{match.feed_name || "Manual"}</td>
              <td>{displayDate(match.matched_at)}</td>
              <td>{displayLabel(match.match_status)}</td>
              <td>
                <button className="ti-row-view" onClick={() => onView(match)}>
                  <Eye size={15} /> View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && (
        <div className="ti-empty">
          No threat matches found for these filters.
        </div>
      )}
    </div>
  );
}
