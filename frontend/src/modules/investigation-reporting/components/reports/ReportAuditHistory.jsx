const dt = (value) => value ? new Date(value).toLocaleString() : "—";
export default function ReportAuditHistory({ events = [] }) {
  return <section className="ir-detail-card"><h3>Audit History</h3>{events.length ? <div className="ir-detail-stack">{events.map((event) => <article className="ir-note" key={event.id}><strong>{event.action.replaceAll("_", " ")}</strong><span>{dt(event.created_at)} · {event.actor_id}</span></article>)}</div> : <p className="ir-muted">No audit events are available in this response.</p>}</section>;
}
