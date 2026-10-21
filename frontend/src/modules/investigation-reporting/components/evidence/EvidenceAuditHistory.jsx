import StatusBadge from "../common/StatusBadge";
const dt = (value) => value ? new Date(value).toLocaleString() : "—";
export default function EvidenceAuditHistory({ events = [], reviewOnly = false }) {
  const visibleEvents = reviewOnly ? events.filter((event) => event.action === "review_status_changed") : events;
  return <section className="ir-detail-card"><h3>{reviewOnly ? "Review History" : "Audit History"}</h3>{visibleEvents.length ? <div className="ir-detail-stack">{visibleEvents.map((event) => <article className="ir-note" key={event.id}><div className="ir-note-head"><strong>{event.action.replaceAll("_", " ")}</strong><span>{dt(event.created_at)} · {event.actor_id}</span></div>{event.reason && <p>Reason: {event.reason}</p>}{event.after_data?.review_status && <StatusBadge status={event.after_data.review_status}/>}<details><summary>Event details</summary><pre className="ir-pre">{JSON.stringify({ before: event.before_data, after: event.after_data }, null, 2)}</pre></details></article>)}</div> : <p className="ir-muted">No {reviewOnly ? "review" : "audit"} events have been recorded.</p>}</section>;
}
