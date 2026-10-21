import { Check, CircleHelp, TriangleAlert, X } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import { displayDate } from "../../types";

const icons = { healthy: Check, degraded: TriangleAlert, unavailable: X, unknown: CircleHelp };
export default function SystemHealthPanel({ data }) {
  return <section className="asa-health-panel"><div className="asa-panel-heading"><div><h2>Service status</h2><p>Sanitized results from available health checks.</p></div><StatusBadge status={data?.overall_status || "unknown"}/></div><div className="asa-health-grid">{(data?.services || []).map((service) => { const Icon = icons[service.status] || CircleHelp; return <article className="asa-health-card" key={service.name}><div><span className={`asa-health-icon asa-health-icon--${service.status}`}><Icon size={17}/></span><StatusBadge status={service.status}/></div><strong>{service.name}</strong><p>{service.description}</p><small>Checked {displayDate(service.last_checked)}</small>{service.message && <small className="asa-health-message">{service.message}</small>}</article>; })}</div></section>;
}
