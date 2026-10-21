import { THREAT_SEVERITIES, displayLabel } from "../types/threatIntelligence";
export default function ThreatSeverityDistribution({ items = [] }) {
  const lookup = Object.fromEntries(
    items.map((row) => [row.severity, row.count]),
  );
  const total =
    Object.values(lookup).reduce((sum, count) => sum + count, 0) || 1;
  return (
    <section className="ti-panel">
      <header>
        <div>
          <h2>Severity Distribution</h2>
          <p>Threat match severity</p>
        </div>
      </header>
      <div className="ti-bars">
        {THREAT_SEVERITIES.slice()
          .reverse()
          .map((severity) => (
            <div className="ti-bar-row" key={severity}>
              <span>{displayLabel(severity)}</span>
              <div>
                <i
                  className={`ti-severity-fill ti-severity-fill--${severity}`}
                  style={{
                    width: `${((lookup[severity] || 0) / total) * 100}%`,
                  }}
                />
              </div>
              <b>{lookup[severity] || 0}</b>
            </div>
          ))}
      </div>
    </section>
  );
}
