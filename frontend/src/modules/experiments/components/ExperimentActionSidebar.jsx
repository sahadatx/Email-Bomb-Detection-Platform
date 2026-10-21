import { X } from "lucide-react";
import { createPortal } from "react-dom";
import { formatDate, formatPercent } from "../types";
import ExperimentStatusBadge from "./ExperimentStatusBadge";

export default function ExperimentActionSidebar({ item, onClose }) {
  if (!item) return null;
  return createPortal(<>
    <button className="ex-sidebar-backdrop" type="button" aria-label="Close experiment details" onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 1198, border: 0, background: "rgb(16 24 40 / 35%)" }}/>
    <aside className="ex-action-sidebar" role="dialog" aria-modal="true" aria-label={`${item.name} details`} style={{ position: "fixed", zIndex: 1199, inset: "0 0 0 auto", width: "min(420px, 94vw)", height: "100dvh", maxHeight: "none", overflow: "auto", padding: 20, border: 0, borderLeft: "1px solid #e3e8ef", borderRadius: 0, background: "#fff", boxShadow: "-14px 0 42px rgb(16 24 40 / 18%)" }}>
      <header className="ex-action-sidebar-heading"><div><h3>{item.name}</h3><small>{item.code || "Experiment details"}</small></div><button type="button" onClick={onClose} aria-label="Close"><X size={17}/></button></header>
      <dl className="ex-sidebar-details">
        <dt>Experiment ID</dt><dd>{item.id}</dd>
        <dt>Status</dt><dd><ExperimentStatusBadge status={item.status}/></dd>
        <dt>Model</dt><dd>{item.model_name || "—"} · {item.algorithm || "—"}</dd>
        <dt>Dataset</dt><dd>{item.dataset_name || "—"} · v{item.dataset_version_number ?? "—"} {item.dataset_version_name || ""}</dd>
        <dt>Evaluation split</dt><dd>{item.evaluation_split || "validation"}</dd>
        <dt>Accuracy</dt><dd>{formatPercent(item.accuracy ?? item.metrics?.accuracy)}</dd>
        <dt>Created</dt><dd>{formatDate(item.created_at)}</dd>
        {item.description && <><dt>Description</dt><dd>{item.description}</dd></>}
      </dl>
      {item.latest_run && <section className="ex-sidebar-run"><h4>Latest run</h4><p>{item.latest_run.id}</p><p>{item.latest_run.progress_percent ?? 0}% complete</p></section>}
    </aside>
  </>, document.body);
}
