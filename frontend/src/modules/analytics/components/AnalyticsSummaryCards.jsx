import { Activity, Mail, ShieldAlert, ShieldCheck } from "lucide-react";
import { formatCount } from "../types";

const cards = [
  ["Total Emails", "total_emails", Mail, "Completed detections in this range"],
  ["Bomb Emails", "bomb_emails", ShieldAlert, "Predicted as email bomb"],
  ["Detection Rate", "detection_rate", Activity, "Bomb predictions / detections"],
  ["High Risk Emails", "high_risk_emails", ShieldCheck, "High and Critical risk"],
];

export default function AnalyticsSummaryCards({ data, loading }) {
  return <section className="an-summary-grid">{cards.map(([label, key, Icon, description]) => {
    const metric = data?.[key];
    const value = loading ? "…" : metric?.value == null ? "—" : key === "detection_rate" ? `${metric.value}%` : formatCount(metric.value);
    return <article className="an-summary-card" key={key}><span className="an-card-icon"><Icon size={18}/></span><div><span className="an-summary-label">{label}</span><strong>{value}</strong><small>{metric?.description || description}</small></div></article>;
  })}</section>;
}
