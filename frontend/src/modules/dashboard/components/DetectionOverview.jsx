import { CheckCircle2 } from "lucide-react";
import { formatNumber } from "../utils/dashboardFormatters";

export default function DetectionOverview({ items = [] }) {
  const counts = Object.fromEntries(
    items.map((item) => [item.classification, item.count]),
  );
  const total = (counts.normal || 0) + (counts.bomb || 0);
  return (
    <section className="dashboard-panel dashboard-classification-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">Detection summary</span>
          <h2>Classification breakdown</h2>
        </div>
        <CheckCircle2 size={18} />
      </div>
      <div className="dashboard-classification-total">
        <strong>{formatNumber(total)}</strong>
        <span>completed detections</span>
      </div>
      <div className="dashboard-classification-row">
        <span className="dashboard-dot dot-normal" />
        Normal<strong>{formatNumber(counts.normal || 0)}</strong>
        <div className="dashboard-mini-track">
          <i
            style={{
              width: `${total ? ((counts.normal || 0) / total) * 100 : 0}%`,
            }}
          />
        </div>
      </div>
      <div className="dashboard-classification-row">
        <span className="dashboard-dot dot-bomb" />
        Bomb<strong>{formatNumber(counts.bomb || 0)}</strong>
        <div className="dashboard-mini-track">
          <i
            style={{
              width: `${total ? ((counts.bomb || 0) / total) * 100 : 0}%`,
            }}
          />
        </div>
      </div>
    </section>
  );
}
