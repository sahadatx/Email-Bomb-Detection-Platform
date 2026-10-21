import { X } from "lucide-react";
import { useState } from "react";
import { detectionService } from "../services/detectionService";

export default function DetectionDetailsDrawer({ item, onClose }) {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  if (!item) return null;
  async function exportReport() {
    setExporting(true); setExportError("");
    try {
      const report = await detectionService.report(item.id);
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `detection-${item.id}.json`; anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setExportError(error.message || "Report export failed.");
    } finally { setExporting(false); }
  }
  return <div className="det-overlay" onMouseDown={onClose}><aside className="det-drawer" onMouseDown={(event) => event.stopPropagation()}><header><div><small>DETECTION RECORD</small><h2>{String(item.id).slice(0, 18)}</h2></div><button className="det-icon-btn" onClick={onClose}><X /></button></header><section className="det-drawer-body"><div className={`det-result-banner ${item.predicted_label}`}><small>Prediction</small><strong>{item.predicted_label === "bomb" ? "Email Bomb" : item.predicted_label === "normal" ? "Normal" : "Unavailable"}</strong></div><div className="det-detail-grid"><div><small>Risk score</small><b>{item.risk?.score == null ? "Unavailable" : `${item.risk.score}/100`}</b></div><div><small>Risk level</small><b>{item.risk?.level || "Unavailable"}</b></div><div><small>Confidence</small><b>{item.confidence == null ? "Unavailable" : `${(item.confidence * 100).toFixed(1)}%`}</b></div><div><small>Model version</small><b>{item.model_name} · v{item.version}</b></div><div><small>Sender</small><b>{item.sender || "—"}</b></div><div><small>Detected at</small><b>{item.created_at ? new Date(item.created_at).toLocaleString() : "—"}</b></div></div>{item.risk?.factors?.length > 0 && <section><h3 id="det-evidence">Risk factors & evidence</h3>{item.risk.factors.map((factor, i) => <p className="det-factor" key={`${factor.name}-${i}`}><span>{factor.name}</span><b>{factor.value} · {factor.impact}</b></p>)}</section>}<section><h3>Behavioral analysis</h3><p>{item.behavioral?.summary || "Not run for this detection."}</p>{(item.behavioral?.anomalies || []).map((anomaly, i) => <p className="det-factor" key={i}><span>{anomaly.pattern}</span><b>{anomaly.severity}</b></p>)}</section>{item.feature_snapshot && Object.keys(item.feature_snapshot).length > 0 && <details><summary>Feature snapshot</summary><pre>{JSON.stringify(item.feature_snapshot, null, 2)}</pre></details>}{exportError && <div className="det-error">{exportError}</div>}</section><footer><button className="det-secondary" disabled={exporting || !item.id} onClick={exportReport}>{exporting ? "Exporting…" : "Export JSON"}</button><button className="det-secondary" onClick={onClose}>Close</button></footer></aside></div>;
}
