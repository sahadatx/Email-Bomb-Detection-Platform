import {
  Activity,
  AlertTriangle,
  Database,
  RadioTower,
  ShieldAlert,
} from "lucide-react";

const ICONS = [Database, RadioTower, Activity, ShieldAlert];
export default function ThreatSummaryCards({ items = [], loading = false }) {
  return (
    <section className="ti-summary-grid">
      {items.map((item, index) => {
        const Icon = ICONS[index] || AlertTriangle;
        return (
          <article
            className={`ti-summary-card ti-summary-card--${index}`}
            key={item.label}
          >
            <span className="ti-summary-icon">
              <Icon size={18} />
            </span>
            <span className="ti-summary-label">{item.label}</span>
            <strong>
              {loading ? "…" : Number(item.value || 0).toLocaleString()}
            </strong>
            <small>{item.caption}</small>
          </article>
        );
      })}
    </section>
  );
}
