import { displayDate, displayLabel } from "../types/threatIntelligence";
export default function FeedSyncHistory({ items = [] }) {
  return items.length ? (
    <ol className="ti-sync-list">
      {items.map((item) => (
        <li key={item.id}>
          <span className={`ti-status ti-status--${item.status}`}>
            {displayLabel(item.status)}
          </span>
          <span>
            {Number(item.imported_count).toLocaleString()} new indicators
          </span>
          <time>{displayDate(item.started_at)}</time>
          {item.error_summary && <p>{item.error_summary}</p>}
        </li>
      ))}
    </ol>
  ) : (
    <div className="ti-empty">No synchronization history yet.</div>
  );
}
