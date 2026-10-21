import { ArrowUpRight, Bell, Settings2, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { formatDate } from "../utils/dashboardFormatters";

export default function RecentActivity({ items = [] }) {
  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">Platform events</span>
          <h2>Recent activity</h2>
        </div>
      </div>
      {items.length ? (
        <div className="dashboard-activity-list">
          {items.map((item) => {
            const Icon =
              item.category === "security"
                ? ShieldCheck
                : item.source?.toLowerCase().includes("auth")
                  ? Bell
                  : Settings2;
            return (
              <Link
                className="dashboard-activity-row"
                to={item.href || "/audit"}
                key={`${item.category}-${item.id}`}
              >
                <span
                  className={`dashboard-activity-icon category-${item.category}`}
                >
                  <Icon size={15} />
                </span>
                <span className="dashboard-activity-copy">
                  <strong>{item.title}</strong>
                  <small>
                    {item.actor || item.source}
                    {item.target ? ` · ${item.target}` : ""}
                  </small>
                </span>
                <time>{formatDate(item.occurred_at)}</time>
                <ArrowUpRight size={14} />
              </Link>
            );
          })}
        </div>
      ) : (
        <div className="dashboard-inline-empty">
          No audit or security events in this time range.
        </div>
      )}
    </section>
  );
}
