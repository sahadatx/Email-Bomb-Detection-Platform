export default function TriggeredRuleList({ rules = [] }) {
  return <section className="ir-detail-card"><h3>Triggered Risk Factors</h3>{rules.length ? <ul className="ir-signal-list">{rules.map((item, index) => <li key={item.id || item.code || index}><strong>{item.name || item.factor || item.rule_name || "Risk signal"}</strong><span>{item.description || item.value || item.impact || "Persisted by risk analysis"}</span></li>)}</ul> : <p className="ir-muted">The Risk service did not persist contributing factors for this detection.</p>}</section>;
}
