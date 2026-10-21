import StatusBadge from "../common/StatusBadge";
export default function ModelInformation({ detection }) {
  const explanation = detection.explanation || {};
  return <section className="ir-detail-card"><h3>Model Information</h3><dl className="ir-dl"><dt>Model</dt><dd>{detection.model_name || "—"}</dd><dt>Algorithm</dt><dd>{detection.algorithm || "—"}</dd><dt>Model type</dt><dd>{detection.model_type || "—"}</dd><dt>Version</dt><dd>{detection.version || "—"}</dd><dt>Method</dt><dd>{explanation.method || "Unavailable"}</dd><dt>Availability</dt><dd><StatusBadge status={explanation.status}/></dd></dl>{explanation.limitations && <p className="ir-muted">{explanation.limitations}</p>}</section>;
}
