import { Activity, Check, CircleHelp, X } from "lucide-react";
import { statusLabel } from "../utils/dashboardFormatters";

function StatusIcon({ status }) {
  if (status === "healthy" || status === "connected" || status === "ready")
    return <Check size={14} />;
  if (status === "unavailable") return <X size={14} />;
  return <CircleHelp size={14} />;
}

export default function SystemHealth({ health }) {
  const components = health?.components || [];
  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">Platform status</span>
          <h2>System health</h2>
        </div>
        <Activity size={18} />
      </div>
      {components.length ? (
        <div className="dashboard-health-list">
          {components.map((item) => (
            <div className="dashboard-health-row" key={item.name}>
              <span className={`dashboard-health-icon is-${item.status}`}>
                <StatusIcon status={item.status} />
              </span>
              <span className="dashboard-health-copy">
                <strong>{item.name}</strong>
                <small>{item.description}</small>
                {item.message && (
                  <small className="dashboard-health-message">
                    {item.message}
                  </small>
                )}
              </span>
              <span className={`dashboard-health-status is-${item.status}`}>
                {statusLabel(item.status)}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="dashboard-inline-empty">
          Health checks are unavailable.
        </div>
      )}
    </section>
  );
}
