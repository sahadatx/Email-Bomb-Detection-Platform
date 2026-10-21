import { useEffect, useState } from "react";
import { Download, Eye, FilePenLine } from "lucide-react";
import { Link } from "react-router-dom";
import DetailsDrawer from "../common/DetailsDrawer";
import StatusBadge from "../common/StatusBadge";
import ReportPreview from "./ReportPreview";
import ReportAuditHistory from "./ReportAuditHistory";
import ReportVersionList from "./ReportVersionList";

const dt = (value) => value ? new Date(value).toLocaleString() : "—";
const TABS = [["overview", "Overview"], ["preview", "Preview"], ["versions", "Versions"], ["audit", "Audit History"]];

export default function ReportDetailsDrawer({ open, report, loading, error, audit, activeTab = "overview", onTab, onClose, onEdit, onGenerate, onDownload, onDuplicate, onArchive, onOpenPage, canManage, canEditDraft, canArchive, canReadAudit = false }) {
  const [tab, setTab] = useState(activeTab);
  useEffect(() => setTab(activeTab), [activeTab, report?.id]);
  const selectTab = (next) => { setTab(next); onTab?.(next); };
  if (!report) return <DetailsDrawer open={open} title="Report Details" onClose={onClose} loading={loading} error={error}/>;

  return <DetailsDrawer open={open} title="Report Details" description={`${report.title} · ${String(report.id).slice(0, 12)}…`} onClose={onClose} loading={loading} error={error} wide footer={<>
    {onOpenPage && <Link className="ir-button ir-button--quiet" to={`/reports/${report.id}`}>Open full page</Link>}
    {canEditDraft && report.status === "draft" && <button className="ir-button ir-button--secondary" onClick={onEdit}><FilePenLine size={15}/> Edit Draft</button>}
    {report.status === "generated" && <button className="ir-button ir-button--secondary" onClick={onDownload}><Download size={15}/> Download {report.output_format?.toUpperCase()}</button>}
    {canManage && ["draft", "failed"].includes(report.status) && <button className="ir-button ir-button--primary" onClick={onGenerate}>{report.status === "failed" ? "Retry Generation" : "Generate Report"}</button>}
    {canManage && <button className="ir-button ir-button--secondary" onClick={onDuplicate}>Duplicate</button>}
    {canArchive && report.status !== "archived" && <button className="ir-button ir-button--danger" onClick={onArchive}>Archive</button>}
  </>}>
    <nav className="ir-tabs" aria-label="Report details sections">{TABS.filter(([key]) => key !== "audit" || canReadAudit).map(([key, label]) => <button type="button" key={key} className={tab === key ? "is-active" : ""} onClick={() => selectTab(key)}>{label}</button>)}</nav>
    {tab === "overview" && <div className="ir-detail-stack"><section className="ir-detail-card"><h3>Report Information</h3><dl className="ir-dl"><dt>ID</dt><dd>{report.id}</dd><dt>Type</dt><dd>{report.report_type}</dd><dt>Format</dt><dd>{report.output_format?.toUpperCase()}</dd><dt>Status</dt><dd><StatusBadge status={report.status}/></dd><dt>Created by</dt><dd>{report.created_by}</dd><dt>Created</dt><dd>{dt(report.created_at)}</dd><dt>Updated</dt><dd>{dt(report.updated_at)}</dd><dt>Generated</dt><dd>{dt(report.generated_at)}</dd><dt>Revision</dt><dd>{report.version}</dd><dt>Detection records</dt><dd>{report.detection_ids?.length || 0}</dd><dt>Sections</dt><dd>{report.sections?.map((section) => section.replaceAll("_", " ")).join(", ") || "—"}</dd></dl>{report.error_summary && <div className="ir-alert">{report.error_summary}</div>}</section><section className="ir-detail-card"><h3>Included Detections</h3>{report.detection_ids?.length ? report.detection_ids.map((id) => <div className="ir-list-row" key={id}><span>{id}</span><Link to={`/detection/history?detection_id=${id}`}>View detection</Link></div>) : <p className="ir-muted">No detection records linked.</p>}</section></div>}
    {tab === "preview" && (report.snapshot ? <ReportPreview snapshot={report.snapshot} report={report}/> : <div className="ir-state"><Eye size={24}/><strong>No generated preview is available</strong><span>A generated preview will appear here when available.</span>{canEditDraft && report.status === "draft" && <button className="ir-button ir-button--primary" onClick={onEdit}><FilePenLine size={15}/> Edit Draft & Preview</button>}</div>)}
    {tab === "versions" && <ReportVersionList report={report}/>}
    {tab === "audit" && canReadAudit && <ReportAuditHistory events={audit || []}/>}
  </DetailsDrawer>;
}
