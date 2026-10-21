import { formatNumber } from "../utils/dashboardFormatters";

const levels = ["critical", "high", "medium", "low"];
export default function RiskDistributionChart({ items = [] }) {
  const counts = Object.fromEntries(
    items.map((item) => [item.risk_level, item.count]),
  );
  const max = Math.max(1, ...levels.map((level) => counts[level] || 0));
  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">Risk overview</span>
          <h2>Severity distribution</h2>
        </div>
      </div>
      <div className="dashboard-risk-list">
        {levels.map((level) => (
          <div className={`dashboard-risk-row risk-${level}`} key={level}>
            <span className="dashboard-risk-name">
              <i />
              {level}
            </span>
            <div className="dashboard-risk-track">
              <i style={{ width: `${((counts[level] || 0) / max) * 100}%` }} />
            </div>
            <strong>{formatNumber(counts[level] || 0)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
