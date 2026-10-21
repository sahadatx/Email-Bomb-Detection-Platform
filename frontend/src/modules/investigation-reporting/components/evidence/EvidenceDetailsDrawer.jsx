import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DetailsDrawer from "../common/DetailsDrawer";
import StatusBadge from "../common/StatusBadge";
import EvidenceRelationships from "./EvidenceRelationships";
import EvidenceProvenance from "./EvidenceProvenance";
import EvidenceAuditHistory from "./EvidenceAuditHistory";

const dt = (value) => value ? new Date(value).toLocaleString() : "—";
const TABS = [["overview", "Overview"], ["relationships", "Relationships"], ["review", "Review History"], ["audit", "Audit History"]];

export default function EvidenceDetailsDrawer({ open, data, loading, error, activeTab = "overview", onClose, onEdit, onReview, canManage, canReadAudit = false }) {
  const [tab, setTab] = useState(activeTab);
  useEffect(() => setTab(activeTab), [activeTab, data?.evidence?.id]);
  const evidence = data?.evidence;
  return <DetailsDrawer open={open} title="Evidence Details" description={evidence?.name || "Evidence record"} onClose={onClose} loading={loading} error={error} footer={evidence && <><Link className="ir-button ir-button--secondary" to={`/detection/history?detection_id=${evidence.detection_id}`}>View Detection</Link>{canManage && <><button className="ir-button ir-button--secondary" onClick={onEdit}>Edit</button><button className="ir-button ir-button--primary" onClick={onReview}>Change Status</button></>}</>}>
    {evidence && <><nav className="ir-tabs" aria-label="Evidence detail sections">{TABS.filter(([key]) => key !== "audit" || canReadAudit).map(([key, label]) => <button type="button" key={key} className={tab === key ? "is-active" : ""} onClick={() => setTab(key)}>{label}</button>)}</nav><div className="ir-detail-stack">
      {tab === "overview" && <><section className="ir-detail-card"><h3>Evidence Overview</h3><dl className="ir-dl"><dt>Evidence ID</dt><dd>{evidence.id}</dd><dt>Type</dt><dd>{evidence.evidence_type?.replaceAll("_", " ")}</dd><dt>Status</dt><dd><StatusBadge status={evidence.review_status}/></dd><dt>Collected</dt><dd>{dt(evidence.collected_at || evidence.created_at)}</dd><dt>Created by</dt><dd>{evidence.created_by}</dd><dt>Updated</dt><dd>{dt(evidence.updated_at)}</dd><dt>Description</dt><dd>{evidence.description || "—"}</dd></dl></section><EvidenceProvenance evidence={evidence}/></>}
      {tab === "relationships" && <EvidenceRelationships evidence={evidence}/>}
      {tab === "review" && <EvidenceAuditHistory events={data.history || []} reviewOnly/>}
      {tab === "audit" && canReadAudit && <EvidenceAuditHistory events={data.history || []}/>}
    </div></>}
  </DetailsDrawer>;
}
