const COLORS = { normal: "#3278e5", bomb: "#e45858" };

export default function EmailActivityChart({ items = [] }) {
  const width = 760;
  const height = 220;
  const padX = 38;
  const padY = 20;
  const maximum = Math.max(
    1,
    ...items.flatMap((point) => [point.normal || 0, point.bomb || 0]),
  );
  const x = (i) =>
    padX +
    (items.length <= 1 ? 0 : (i * (width - padX * 2)) / (items.length - 1));
  const y = (value) => height - padY - (value / maximum) * (height - padY * 2);
  const path = (key) =>
    items
      .map(
        (point, index) =>
          `${index ? "L" : "M"}${x(index)},${y(point[key] || 0)}`,
      )
      .join(" ");
  return (
    <div className="dashboard-activity-chart">
      <div className="dashboard-chart-legend">
        <span>
          <i className="dashboard-dot dot-normal" />
          Normal detections
        </span>
        <span>
          <i className="dashboard-dot dot-bomb" />
          Bomb detections
        </span>
      </div>
      {items.length ? (
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="Detection volume over time"
        >
          {[0, 1, 2, 3].map((line) => {
            const yy = padY + (line * (height - padY * 2)) / 3;
            return (
              <g key={line}>
                <line
                  x1={padX}
                  x2={width - padX}
                  y1={yy}
                  y2={yy}
                  className="dashboard-chart-gridline"
                />
                <text x="2" y={yy + 4} className="dashboard-chart-axis">
                  {Math.round((maximum * (3 - line)) / 3)}
                </text>
              </g>
            );
          })}
          <path
            d={path("normal")}
            fill="none"
            stroke={COLORS.normal}
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          <path
            d={path("bomb")}
            fill="none"
            stroke={COLORS.bomb}
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {items.map((point, index) => (
            <g key={point.timestamp}>
              <circle
                cx={x(index)}
                cy={y(point.normal || 0)}
                r="3.5"
                fill={COLORS.normal}
              >
                <title>
                  {point.timestamp}: normal {point.normal}
                </title>
              </circle>
              <circle
                cx={x(index)}
                cy={y(point.bomb || 0)}
                r="3.5"
                fill={COLORS.bomb}
              >
                <title>
                  {point.timestamp}: bomb {point.bomb}
                </title>
              </circle>
            </g>
          ))}
          <text x={padX} y={height - 1} className="dashboard-chart-axis">
            {items[0]?.timestamp}
          </text>
          <text
            x={width - padX}
            y={height - 1}
            textAnchor="end"
            className="dashboard-chart-axis"
          >
            {items.at(-1)?.timestamp}
          </text>
        </svg>
      ) : (
        <div className="dashboard-chart-empty">
          No completed detection activity in this period.
        </div>
      )}
      <p className="dashboard-chart-footnote">
        Activity is grouped from completed detection records; it does not
        represent unprocessed email intake.
      </p>
    </div>
  );
}
