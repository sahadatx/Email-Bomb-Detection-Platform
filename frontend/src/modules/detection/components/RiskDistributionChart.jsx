import { RISK_LEVELS } from "../types";

export default function RiskDistributionChart({ distribution = {} }) {
  const maximum = Math.max(1, ...Object.values(distribution).map((value) => Number(value) || 0));
  const total = Object.values(distribution).reduce((sum, value) => sum + (Number(value) || 0), 0);

  if (!total) return <div className="det-empty">No risk assessments have been recorded.</div>;

  return (
    <div className="det-risk-bars">
      {RISK_LEVELS.map((level) => {
        const count = Number(distribution[level]) || 0;
        return (
          <div className="det-risk-row" key={level}>
            <span>{level}</span>
            <div className="det-risk-track" aria-label={`${count} ${level} risk records`}>
              <i className={`risk-fill ${level}`} style={{ width: `${(count / maximum) * 100}%` }} />
            </div>
            <b>{count}</b>
          </div>
        );
      })}
    </div>
  );
}
