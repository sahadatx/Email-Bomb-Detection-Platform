import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../../core/auth/AuthProvider";
import InvestigationPageHeader from "../components/common/InvestigationPageHeader";
import ConfirmDialog from "../components/common/ConfirmDialog";
import ReportGenerationDialog from "../components/reports/ReportGenerationDialog";
import ReportDetailsDrawer from "../components/reports/ReportDetailsDrawer";
import { reportService } from "../services/reportService";
import { investigationError } from "../types";
import { getInvestigationAccess, permissionMessage } from "../permissions";

export default function ReportDetailsPage() {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const access = getInvestigationAccess(user);
  const canManage = access.canManage;
  const isAdmin = access.isAdmin;
  const [report, setReport] = useState(null);
  const [audit, setAudit] = useState([]);
  const [detailsTab, setDetailsTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setReport(await reportService.detail(reportId)); if (isAdmin) setAudit(await reportService.audit(reportId) || []); }
    catch (cause) { setError(investigationError(cause)); }
    finally { setLoading(false); }
  }, [reportId, isAdmin]);
  useEffect(() => { load(); }, [load]);
  async function action(kind) {
    if (!report || busy) return;
    setBusy(true); setError("");
    try {
      if (kind === "generate") { const updated = await reportService.generate(report.id); setReport(updated); if (updated.status === "generated") setDetailsTab("preview"); setToast(updated.status === "generated" ? "Report generated." : updated.error_summary || "Report generation failed."); }
      if (kind === "archive") { setReport(await reportService.archive(report.id)); setToast("Report archived."); }
      if (kind === "duplicate") { const copy = await reportService.duplicate(report.id); navigate(`/reports/${copy.id}`, { replace: true }); setReport(copy); setToast("Draft copy created."); }
      if (kind === "download") await reportService.download(report.id, report.output_format);
      setConfirm(""); if (kind !== "duplicate") await load();
    } catch (cause) { setError(investigationError(cause)); }
    finally { setBusy(false); }
  }
  return <main className="ir-page"><InvestigationPageHeader title="Report Details" description="Review report metadata, generated snapshot and audit history." onRefresh={load} loading={loading} actions={<Link className="ir-button ir-button--secondary" to="/reports">Back to Reports</Link>}/>{toast && <div className="ir-notice ir-notice--success" role="status">{toast}<button onClick={() => setToast("")}>Dismiss</button></div>}{error && !report && <div className="ir-alert" role="alert">{error}<button onClick={load}>Retry</button></div>}<section className="ir-panel"><div className="ir-state">{loading ? "Loading report…" : report ? `Report ${report.id}` : "Report could not be loaded."}</div></section>
    {!canManage && <p className="ir-permission-hint">You have read-only report access. Draft creation and generation require an analyst role. {permissionMessage("modify this report")}</p>}
    <ReportDetailsDrawer open={Boolean(report) || loading} report={report} loading={loading} error={error} audit={audit} activeTab={detailsTab} onTab={setDetailsTab} onClose={() => navigate("/reports")} canManage={canManage} canEditDraft={access.canEditReports} canArchive={access.canArchiveReports} canReadAudit={access.canReadAudit} onEdit={() => navigate(`/reports?edit=${report.id}`)} onGenerate={() => setConfirm("generate")} onDownload={() => action("download")} onDuplicate={() => action("duplicate")} onArchive={() => setConfirm("archive")}/>
    {confirm === "generate" ? <ReportGenerationDialog open report={report} busy={busy} onCancel={() => setConfirm("")} onConfirm={() => action("generate")}/> : <ConfirmDialog open={confirm === "archive"} title="Archive report?" message={`Archive “${report?.title || "this report"}”? It will remain available in the report library.`} confirmLabel="Archive Report" busy={busy} onCancel={() => setConfirm("")} onConfirm={() => action("archive")}/>}
  </main>;
}
