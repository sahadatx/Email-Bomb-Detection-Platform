import StatusBadge from "../common/StatusBadge";
export default function RiskBreakdown({ risk }) {
  if (!risk) return <section className="ir-detail-card"><h3>Risk Breakdown</h3><p className="ir-muted">Risk assessment is unavailable for this detection.</p></section>;
  return <section className="ir-detail-card"><h3>Risk Breakdown</h3><dl className="ir-dl"><dt>Assessment status</dt><dd><StatusBadge status={risk.status}/></dd><dt>Score</dt><dd>{risk.score == null ? "Unavailable" : `${risk.score}/100`}</dd><dt>Level</dt><dd><StatusBadge status={risk.level}/></dd><dt>Factor count</dt><dd>{risk.factors?.length || 0}</dd></dl></section>;
}
