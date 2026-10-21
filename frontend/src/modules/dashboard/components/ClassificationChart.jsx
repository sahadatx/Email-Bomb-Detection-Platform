import { formatNumber } from "../utils/dashboardFormatters";

export default function ClassificationChart({ items = [] }) {
  const normal =
    items.find((item) => item.classification === "normal")?.count || 0;
  const bomb = items.find((item) => item.classification === "bomb")?.count || 0;
  const total = normal + bomb;
  const normalPct = total ? (normal / total) * 100 : 0;
  return (
    <div
      className="dashboard-classification-chart"
      aria-label={`Normal ${normal}; Bomb ${bomb}`}
    >
      <div
        className="dashboard-donut"
        style={{ "--normal-share": `${normalPct}%` }}
      >
        <div>
          <strong>{formatNumber(total)}</strong>
          <span>Total</span>
        </div>
      </div>
      <div className="dashboard-chart-legend">
        <span>
          <i className="dashboard-dot dot-normal" />
          Normal <b>{formatNumber(normal)}</b>
        </span>
        <span>
          <i className="dashboard-dot dot-bomb" />
          Bomb <b>{formatNumber(bomb)}</b>
        </span>
      </div>
    </div>
  );
}
