import { formatCount } from "../types";

const riskTone = { low: "low", medium: "medium", high: "high", critical: "critical" };
export default function RiskDistribution({ items = [] }) {
  const total = items.reduce((sum, item) => sum + Number(item.count || 0), 0);
  return <section className="an-panel"><header className="an-panel-heading"><div><h2>Risk Distribution</h2><p>Stored risk assessments by severity</p></div></header>{items.length ? <div className="an-distribution">{items.map((item) => { const level = String(item.risk_level || "unknown").toLowerCase(); return <div className="an-distribution-row" key={level}><span>{level[0].toUpperCase() + level.slice(1)}</span><div className="an-track"><i className={`an-fill an-fill--${riskTone[level] || "low"}`} style={{ width: `${total ? Number(item.count || 0) / total * 100 : 0}%` }}/></div><strong>{formatCount(item.count)}</strong></div>; })}</div> : <p className="an-empty">No risk assessments in this range.</p>}</section>;
}
