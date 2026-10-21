import { ArrowUpRight, Mail } from "lucide-react";
import { Link } from "react-router-dom";
import { formatDate } from "../utils/dashboardFormatters";

export default function RecentDetections({ items = [] }) {
  return (
    <section className="dashboard-panel dashboard-table-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">Email security</span>
          <h2>Recent threat detections</h2>
        </div>
        <Link to="/detection/history" className="dashboard-text-link">
          View all <ArrowUpRight size={15} />
        </Link>
      </div>
      {items.length ? (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Classification</th>
                <th>Risk</th>
                <th>Model</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <span className="dashboard-email-cell">
                      <Mail size={15} />
                      <span>
                        <strong>
                          {item.sender || item.email_id || "Email record"}
                        </strong>
                        <small>
                          {item.subject ||
                            `Detection ${String(item.id).slice(0, 8)}`}
                        </small>
                      </span>
                    </span>
                  </td>
                  <td>
                    <span
                      className={`dashboard-tag tag-${item.classification}`}
                    >
                      {item.classification}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`dashboard-tag tag-risk-${item.risk_level || "unknown"}`}
                    >
                      {item.risk_level || "Unavailable"}
                    </span>
                  </td>
                  <td>
                    {item.model_name
                      ? `${item.model_name}${item.model_version ? ` · v${item.model_version}` : ""}`
                      : "—"}
                  </td>
                  <td>{formatDate(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="dashboard-inline-empty">
          No completed detections match the selected filters.
        </div>
      )}
    </section>
  );
}
