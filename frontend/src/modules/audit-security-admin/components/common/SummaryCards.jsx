import { Activity, BriefcaseBusiness, CircleAlert, HeartPulse } from "lucide-react";

const icons = { status: Activity, total: BriefcaseBusiness, failed: CircleAlert, services: HeartPulse };
export default function SummaryCards({ items = [], loading = false }) {
  return <section className="asa-summary-grid">{items.map((item, index) => { const Icon = icons[item.icon] || Activity; return <article className={`asa-summary-card asa-summary-card--${index % 4}`} key={item.label}><div><span>{item.label}</span><strong>{loading ? "…" : item.value ?? 0}</strong><small>{item.description}</small></div><i><Icon size={19}/></i></article>; })}</section>;
}
