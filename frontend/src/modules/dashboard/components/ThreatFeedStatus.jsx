import { RadioTower } from "lucide-react";
import { Link } from "react-router-dom";
import { formatDate, statusLabel } from "../utils/dashboardFormatters";

export default function ThreatFeedStatus({ data }) {
  return (
    <section className="dashboard-panel dashboard-compact-status">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">External intelligence</span>
          <h2>Threat feeds</h2>
        </div>
        <RadioTower size={18} />
      </div>
      <div className="dashboard-model-summary">
        <span
          className={`dashboard-status-dot is-${data?.status || "unknown"}`}
        />
        <strong>{statusLabel(data?.status)}</strong>
        <small>
          {data?.active_feeds || 0} active of {data?.total_feeds || 0} feeds
        </small>
      </div>
      {data?.feeds?.length ? (
        data.feeds.slice(0, 3).map((feed) => (
          <div className="dashboard-feed-row" key={feed.id}>
            <span>
              <strong>{feed.name}</strong>
              <small>Last sync {formatDate(feed.last_sync_at)}</small>
            </span>
            <em className={`is-${feed.sync_status}`}>
              {statusLabel(feed.sync_status)}
            </em>
          </div>
        ))
      ) : (
        <p className="dashboard-muted">
          No feed synchronization records are available.
        </p>
      )}
      {data?.message && (
        <p className="dashboard-health-message">{data.message}</p>
      )}
      <Link className="dashboard-text-link" to="/threat-intelligence/feeds">
        Manage threat feeds →
      </Link>
    </section>
  );
}
