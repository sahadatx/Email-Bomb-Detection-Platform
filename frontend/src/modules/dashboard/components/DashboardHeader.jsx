import { Activity, Clock3, RefreshCw } from "lucide-react";
import { formatDate, statusLabel } from "../utils/dashboardFormatters";

export default function DashboardHeader({ data, loading, onRefresh }) {
  const status = data?.system_health?.overall_status || "unknown";
  return (
    <header className="dashboard-header">
      <div>
        <div className="dashboard-eyebrow">
          <Activity size={15} /> Security Operations
        </div>
        <h1>Dashboard</h1>
        <p>
          Email security, detection activity and platform health at a glance.
        </p>
        <div className="dashboard-updated">
          <Clock3 size={14} /> Last updated {formatDate(data?.generated_at)}
        </div>
      </div>
      <div className="dashboard-header-actions">
        <span className={`dashboard-system-pill is-${status}`}>
          <i />
          {statusLabel(status)}
        </span>
        <button
          className="dashboard-button dashboard-button-secondary"
          type="button"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw size={15} className={loading ? "dashboard-spin" : ""} />{" "}
          Refresh
        </button>
      </div>
    </header>
  );
}
