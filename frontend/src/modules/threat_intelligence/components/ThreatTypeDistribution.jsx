import { displayLabel } from "../types/threatIntelligence";
export default function ThreatTypeDistribution({ items = [] }) {
  const total = items.reduce((sum, row) => sum + row.count, 0) || 1;
  return (
    <section className="ti-panel">
      <header>
        <div>
          <h2>Threat Types</h2>
          <p>IOC distribution</p>
        </div>
      </header>
      {items.length ? (
        <div className="ti-bars">
          {items.map((row) => (
            <div className="ti-bar-row" key={row.type}>
              <span>{displayLabel(row.type)}</span>
              <div>
                <i style={{ width: `${(row.count / total) * 100}%` }} />
              </div>
              <b>{row.count}</b>
            </div>
          ))}
        </div>
      ) : (
        <div className="ti-empty">No matched indicator types yet.</div>
      )}
    </section>
  );
}
