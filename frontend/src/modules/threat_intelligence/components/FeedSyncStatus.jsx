import { displayDate, displayLabel } from "../types/threatIntelligence";
export default function FeedSyncStatus({ feed }) {
  return (
    <dl className="ti-definition-list">
      <dt>Status</dt>
      <dd>
        <span className={`ti-status ti-status--${feed.sync_status}`}>
          {displayLabel(feed.sync_status)}
        </span>
      </dd>
      <dt>Last Sync</dt>
      <dd>{displayDate(feed.last_sync_at)}</dd>
      <dt>Next Scheduled</dt>
      <dd>{displayDate(feed.next_sync_at)}</dd>
      <dt>Imported Indicators</dt>
      <dd>{Number(feed.imported_indicator_count || 0).toLocaleString()}</dd>
      {feed.latest_error && (
        <>
          <dt>Latest Error</dt>
          <dd className="ti-feed-error">{feed.latest_error}</dd>
        </>
      )}
    </dl>
  );
}
