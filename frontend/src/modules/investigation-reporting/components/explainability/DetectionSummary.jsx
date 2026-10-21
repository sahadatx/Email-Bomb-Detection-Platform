import StatusBadge from "../common/StatusBadge";
const date = (value) => value ? new Date(value).toLocaleString() : "—";
export default function DetectionSummary({ detection }) {
  return <section className="ir-detail-card"><h3>Detection Summary</h3><dl className="ir-dl"><dt>Detection ID</dt><dd>{detection.id}</dd><dt>Source</dt><dd>{detection.email_id || detection.input_id || "—"}</dd><dt>Prediction</dt><dd><StatusBadge status={detection.predicted_label}/></dd><dt>Confidence</dt><dd>{detection.confidence == null ? "Unavailable" : `${(detection.confidence * 100).toFixed(2)}%`}</dd><dt>Risk</dt><dd>{detection.risk?.score == null ? "Unavailable" : `${detection.risk.score}/100 · ${detection.risk.level}`}</dd><dt>Status</dt><dd><StatusBadge status={detection.status}/></dd><dt>Detected</dt><dd>{date(detection.created_at)}</dd></dl></section>;
}
