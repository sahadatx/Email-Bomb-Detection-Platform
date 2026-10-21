import StatusBadge from "../common/StatusBadge";
export default function BehavioralSignals({ behavioral }) {
  const signals = behavioral?.anomalies || [];
  return <section className="ir-detail-card"><h3>Behavioral Signals</h3>{!behavioral || behavioral.status === "insufficient_data" ? <p className="ir-muted">Behavioral history is insufficient for a signal summary.</p> : <><p>{behavioral.summary || "No summary provided."}</p><p className="ir-muted">Analysis status: {behavioral.status}</p>{signals.length ? <ul className="ir-signal-list">{signals.map((item, index) => <li key={item.id || index}><strong>{item.name || item.pattern || "Behavioral signal"}</strong><span>{item.description || item.summary || ""}</span><StatusBadge status={item.severity || "unavailable"}/></li>)}</ul> : <p className="ir-muted">No behavioral anomalies were persisted.</p>}</>}</section>;
}
