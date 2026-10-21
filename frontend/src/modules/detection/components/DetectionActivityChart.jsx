export default function DetectionActivityChart({ points = [], valueKey = "count", valueLabel = "detections" }) {
  if (!points.length) {
    return <div className="det-empty">No activity has been recorded for this period.</div>;
  }

  const maximum = Math.max(1, ...points.map((point) => Number(point[valueKey]) || 0));

  return (
    <div className="det-chart" role="img" aria-label={`${valueLabel} over time`}>
      {points.map((point) => {
        const value = Number(point[valueKey]) || 0;
        const height = value === 0 ? 0 : Math.max(5, (value / maximum) * 100);
        return (
          <div className="det-bar-col" key={point.time} title={`${point.time}: ${value} ${valueLabel}`}>
            <span>{value}</span>
            <div style={{ height: `${height}%` }} />
            <small>{point.time.slice(5)}</small>
          </div>
        );
      })}
    </div>
  );
}
