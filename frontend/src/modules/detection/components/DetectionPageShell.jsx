import { Link } from "react-router-dom";
import { RefreshCw, Zap } from "lucide-react";
import DetectionDetailsDrawer from "./DetectionDetailsDrawer";
import { useAuth } from "../../../core/auth/AuthProvider";

const NAVIGATION = [
  ["/detection", "overview", "Overview"],
  ["/detection/new", "new", "New Detection"],
  ["/detection/history", "history", "History"],
  ["/detection/risk", "risk", "Risk Analysis"],
  ["/detection/behavior", "behavior", "Behavioral Analysis"],
  ["/detection/settings", "settings", "Settings"],
];

export default function DetectionPageShell({
  page,
  title,
  description,
  loading = false,
  error = "",
  onRefresh,
  children,
  selectedDetection,
  onCloseDetection,
}) {
  const { user } = useAuth();
  const navigation = NAVIGATION.filter(([href]) =>
    href === "/detection/settings"
      ? user?.role === "ADMIN"
      : href === "/detection/new"
        ? user?.role !== "VIEWER"
        : true,
  );
  return (
    <main className="detection-page">
      <div className="det-page-head">
        <div>
          <span className="det-eyebrow">DETECTION &amp; RISK ANALYSIS</span>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <div className="det-head-actions">
          {onRefresh && (
            <button className="det-secondary" onClick={onRefresh} disabled={loading}>
              <RefreshCw size={15} />
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          )}
          {page !== "new" && user?.role !== "VIEWER" && (
            <Link className="det-primary" to="/detection/new">
              <Zap size={16} /> New Detection
            </Link>
          )}
        </div>
      </div>

      <nav className="det-tabs" aria-label="Detection module pages">
        {navigation.map(([href, key, label]) => (
          <Link key={key} to={href} className={page === key ? "active" : ""}>
            {label}
          </Link>
        ))}
      </nav>

      {error && (
        <div className="det-error" role="alert">
          <span>{error}</span>
          {onRefresh && <button onClick={onRefresh}>Retry</button>}
        </div>
      )}
      {loading ? <div className="det-loading">Loading detection data…</div> : children}

      <DetectionDetailsDrawer
        item={selectedDetection}
        onClose={onCloseDetection}
      />
    </main>
  );
}
