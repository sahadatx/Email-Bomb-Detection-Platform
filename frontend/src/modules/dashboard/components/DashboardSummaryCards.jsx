import { AlertTriangle, Mail, ScanLine, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { metricValue } from "../utils/dashboardFormatters";

const cards = [
  [
    "total_emails",
    "Total emails",
    "Ingested in the selected period",
    Mail,
    "blue",
  ],
  [
    "emails_analyzed",
    "Emails analyzed",
    "Completed detections",
    ScanLine,
    "violet",
  ],
  [
    "bomb_detected",
    "Bomb detected",
    "Completed bomb classifications",
    AlertTriangle,
    "red",
  ],
  [
    "high_risk_emails",
    "High-risk emails",
    "High and critical risk",
    ShieldAlert,
    "amber",
  ],
  [
    "active_security_alerts",
    "Active security alerts",
    "Unresolved alerts in the selected period",
    ShieldAlert,
    "red",
  ],
];

export default function DashboardSummaryCards({ summary = {} }) {
  return (
    <section className="dashboard-kpi-grid" aria-label="Email security summary">
      {cards.map(([key, title, caption, Icon, color]) => {
        const metric = summary[key];
        const Card = key === "active_security_alerts" ? Link : "article";
        return (
          <Card
            className={`dashboard-kpi-card accent-${color}`}
            key={key}
            {...(key === "active_security_alerts"
              ? { to: "/security-monitoring", "aria-label": `${title}: ${metricValue(metric)}. Open Security Monitoring` }
              : {})}
          >
            <div className="dashboard-kpi-icon">
              <Icon size={18} />
            </div>
            <div className="dashboard-kpi-label">{title}</div>
            <div className="dashboard-kpi-value">{metricValue(metric)}</div>
            <div className="dashboard-kpi-caption">
              {metric?.description || caption}
            </div>
          </Card>
        );
      })}
    </section>
  );
}
