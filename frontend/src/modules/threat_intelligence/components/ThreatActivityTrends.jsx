export default function ThreatActivityTrends({ items = [] }) {
  const max = Math.max(
    1,
    ...items.flatMap((item) => [
      Number(item.matches || 0),
      Number(item.indicators || 0),
    ]),
  );
  return (
    <section className="ti-panel">
      <header>
        <div>
          <h2>Threat Activity Trends</h2>
          <p>Matches and newly added indicators in the selected time range</p>
        </div>
        <div className="ti-chart-legend">
          <span>
            <i className="ti-legend-match" /> Matches
          </span>
          <span>
            <i className="ti-legend-indicator" /> Indicators
          </span>
        </div>
      </header>
      {items.length ? (
        <div className="ti-trend-chart">
          {items.map((item) => (
            <div
              className="ti-trend-column"
              key={item.date}
              title={`${item.matches || 0} matches · ${item.indicators || 0} indicators`}
            >
              <div className="ti-trend-bars">
                <span
                  className="ti-trend-match"
                  style={{
                    height: `${Math.max(3, (Number(item.matches || 0) / max) * 100)}%`,
                  }}
                />
                <span
                  className="ti-trend-indicator"
                  style={{
                    height: `${Math.max(3, (Number(item.indicators || 0) / max) * 100)}%`,
                  }}
                />
              </div>
              <small>
                {new Date(item.date).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })}
              </small>
            </div>
          ))}
        </div>
      ) : (
        <div className="ti-empty">No match activity in this period.</div>
      )}
    </section>
  );
}
