import { useState } from "react";
import RightDrawer from "../common/RightDrawer";
import StatusBadge from "../common/StatusBadge";
import { displayDate } from "../../types";

const tabs = ["Overview", "Metadata", "Related Events", "Audit Context"];
export default function AuditDetailsDrawer({ event, onClose, loading = false }) {
  const [tab, setTab] = useState("Overview");
  if (!event) return null;
  return <RightDrawer open title="Audit Event" description={`${event.action} · ${event.id}`} onClose={onClose} wide>{loading ? <div className="asa-state">Loading event details…</div> : event.detailError ? <div className="asa-error-inline">{event.detailError}</div> : <><nav className="asa-tabs">{tabs.map((value) => <button className={tab === value ? "is-active" : ""} key={value} onClick={() => setTab(value)}>{value}</button>)}</nav>
    {tab === "Overview" && <section className="asa-detail-grid"><span>Event ID</span><code>{event.id}</code><span>Actor</span><strong>{event.actor_name || "System"}</strong><span>Actor Role</span><span>{event.actor_role || "—"}</span><span>Action</span><strong>{event.action}</strong><span>Target</span><span>{event.target_label || event.target_id || "—"}</span><span>Timestamp</span><span>{displayDate(event.created_at)}</span><span>Status</span><StatusBadge status={event.status}/><span>Severity</span><span>{event.severity ? <StatusBadge status={event.severity}/> : "—"}</span><span>IP Address</span><span>{event.ip_address || "—"}</span><span>Source Module</span><span>{event.source}</span></section>}
    {tab === "Metadata" && <div className="asa-panel"><h3>Structured event metadata</h3><pre className="asa-json">{JSON.stringify(event.details || {}, null, 2)}</pre><p>Sensitive fields are redacted by the API.</p></div>}
    {tab === "Related Events" && <div className="asa-stack">{event.related_events?.length ? event.related_events.map((row) => <article key={row.id}><strong>{row.action}</strong><span>{row.actor_name} · {displayDate(row.created_at)}</span></article>) : <p className="asa-muted">No related events were returned.</p>}</div>}
    {tab === "Audit Context" && <section className="asa-detail-grid"><span>Source</span><span>{event.source || "—"}</span><span>Correlation ID</span><code>{event.correlation_id || "Not supplied"}</code><span>Request context</span><span>Only fields returned by the audit API are shown.</span></section>}</>}
  </RightDrawer>;
}
