import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FilePlus2 } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import InvestigationPageHeader from "../components/common/InvestigationPageHeader";
import SummaryCards from "../components/common/SummaryCards";
import SearchFilterBar from "../components/common/SearchFilterBar";
import Pagination from "../components/common/Pagination";
import ErrorState from "../components/common/ErrorState";
import ConfirmDialog from "../components/common/ConfirmDialog";
import DetailsDrawer from "../components/common/DetailsDrawer";
import ReportTable from "../components/reports/ReportTable";
import ReportForm from "../components/reports/ReportForm";
import ReportDetailsDrawer from "../components/reports/ReportDetailsDrawer";
import ReportPreview from "../components/reports/ReportPreview";
import ReportGenerationDialog from "../components/reports/ReportGenerationDialog";
import useInvestigationQuery from "../hooks/useInvestigationQuery";
import useReports from "../hooks/useReports";
import { reportService } from "../services/reportService";
import { REPORT_TYPES, investigationError } from "../types";
import { getInvestigationAccess } from "../permissions";

const DEFAULT_FILTERS = { report_type: "", status: "", output_format: "", created_from: "", created_to: "" };
const EMPTY_FORM = { title: "", description: "", report_type: "investigation", detection_ids: [], sections: ["executive_summary", "detection_summary", "risk_analysis"], output_format: "pdf", analyst_notes: "" };
const PAGE_SIZE = 30;

export default function ReportsPage() {
  const { user } = useAuth();
  const access = getInvestigationAccess(user);
  const canManage = access.canManage;
  const canEditDraft = access.canEditReports;
  const isAdmin = access.isAdmin;
  const [searchParams, setSearchParams] = useSearchParams();
  const query = useInvestigationQuery(DEFAULT_FILTERS, PAGE_SIZE);
  const data = useReports(query);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formInitial, setFormInitial] = useState(EMPTY_FORM);
  const [discardForm, setDiscardForm] = useState(false);
  const [selected, setSelected] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsTab, setDetailsTab] = useState("overview");
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");
  const [audit, setAudit] = useState([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [preview, setPreview] = useState(null);
  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [confirmAction, setConfirmAction] = useState("");
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState("");
  const [toast, setToast] = useState("");

  useEffect(() => {
    const editId = searchParams.get("edit");
    if (!editId) return;
    let active = true;
    reportService.detail(editId).then((record) => { if (active && canEditDraft && record.status === "draft") openEdit(record); }).catch((cause) => { if (active) setActionError(investigationError(cause)); }).finally(() => { if (active) setSearchParams((current) => { current.delete("edit"); return current; }, { replace: true }); });
    return () => { active = false; };
  }, [searchParams, setSearchParams]);

  function openCreate() {
    const relatedId = query.filters.detection_id;
    const values = { ...EMPTY_FORM, detection_ids: relatedId ? [relatedId] : [] }; setSelected(null); setForm(values); setFormInitial(values); setActionError(""); setPreview(null); setFormOpen(true);
  }
  function openEdit(report) {
    const values = { title: report.title, description: report.description || "", report_type: report.report_type, detection_ids: report.detection_ids || [], sections: report.sections || [], output_format: report.output_format, analyst_notes: report.analyst_notes || "" }; setSelected(report); setForm(values); setFormInitial(values); setActionError(""); setPreview(null); setFormOpen(true);
  }
  function requestCloseForm() { if (saving) return; if (JSON.stringify(form) !== JSON.stringify(formInitial)) setDiscardForm(true); else setFormOpen(false); }
  async function openDetails(report, tab = "overview") {
    setDetailsOpen(true); setDetailsTab(tab); setDetailsLoading(true); setDetailsError(""); setSelected(report); setAudit([]);
    try {
      const full = await reportService.detail(report.id); setSelected(full);
      if (isAdmin) setAudit(await reportService.audit(report.id) || []);
    } catch (cause) { setDetailsError(investigationError(cause)); }
    finally { setDetailsLoading(false); }
  }
  async function saveDraft() {
    if (saving) return null;
    setSaving(true); setActionError("");
    try {
      const saved = selected?.id ? await reportService.update(selected.id, form) : await reportService.create(form);
      setSelected(saved); setFormOpen(false); setPreviewOpen(false); setToast("Report draft saved."); setDetailsOpen(true); await data.refresh();
      return saved;
    } catch (cause) { setActionError(investigationError(cause)); }
    finally { setSaving(false); }
  }
  async function submitDraft(event) { event?.preventDefault?.(); await saveDraft(); }
  async function generateReport() {
    if (saving) return;
    setSaving(true); setActionError("");
    try {
      const saved = selected?.id ? await reportService.update(selected.id, form) : await reportService.create(form);
      setSelected(saved);
      const generated = await reportService.generate(saved.id);
      setFormOpen(false); setPreviewOpen(false); setSelected(generated); setDetailsTab("preview"); setDetailsOpen(true);
      setToast(generated.status === "generated" ? "Report generated from a point-in-time snapshot." : `Report generation failed: ${generated.error_summary || "Review report details."}`);
      await data.refresh();
    } catch (cause) { setActionError(investigationError(cause)); }
    finally { setSaving(false); }
  }
  async function previewDraft() {
    if (!form.title.trim() || !form.detection_ids.length || !form.sections.length) { setActionError("Add a title, select at least one detection, and include at least one report section."); return; }
    setPreviewing(true); setPreviewError(""); setActionError("");
    try { setPreview(await reportService.preview(form)); setPreviewOpen(true); }
    catch (cause) { const message = investigationError(cause); setPreviewError(message); setActionError(message); }
    finally { setPreviewing(false); }
  }
  async function performAction(action, target = selected) {
    if (!target?.id || saving) return;
    setSaving(true); setActionError(""); setDetailsError("");
    try {
      if (action === "generate") {
        const result = await reportService.generate(target.id); setSelected(result); setDetailsTab("preview");
        setToast(result.status === "generated" ? "Report generated from a point-in-time snapshot." : `Report generation failed: ${result.error_summary || "Review report details."}`);
      } else if (action === "archive") {
        setSelected(await reportService.archive(target.id)); setToast("Report archived.");
      } else if (action === "duplicate") {
        const copy = await reportService.duplicate(target.id); setSelected(copy); setToast("Draft copy created."); setDetailsOpen(false); openEdit(copy);
      } else if (action === "download") {
        await reportService.download(target.id, target.output_format); setToast("Report download started.");
      }
      setConfirmAction(""); await data.refresh();
    } catch (cause) { const message = investigationError(cause); setActionError(message); setDetailsError(message); }
    finally { setSaving(false); }
  }
  const summary = data.summary || {};

  return <main className="ir-page">
    <InvestigationPageHeader title="Reports" description="Create, preview, generate and export investigation reports from persisted records." onRefresh={data.refresh} loading={data.loading} actions={canManage && <button className="ir-button ir-button--primary" onClick={openCreate}><FilePlus2 size={16}/> Create Report</button>}/>
    {toast && <div className="ir-notice ir-notice--success" role="status">{toast}<button onClick={() => setToast("")}>Dismiss</button></div>}
    <SummaryCards loading={data.loading} items={[["Total Reports", summary.total], ["Generated", summary.generated], ["Drafts", summary.draft], ["Failed", summary.failed]].map(([label, value]) => ({ label, value }))}/>
    <SearchFilterBar className="ir-report-filters" search={query.search} onSearch={query.setSearch} placeholder="Search report ID or title…" onReset={query.reset} showApply={false} count={data.total}>
      <label>Report Type<select value={query.filters.report_type} onChange={(e) => { query.setFilters({ ...query.filters, report_type: e.target.value }); query.setPage(1); }}><option value="">All types</option>{REPORT_TYPES.map((type) => <option value={type} key={type}>{type}</option>)}</select></label>
      <label>Status<select value={query.filters.status} onChange={(e) => { query.setFilters({ ...query.filters, status: e.target.value }); query.setPage(1); }}><option value="">All statuses</option>{["draft", "generated", "failed", "archived"].map((status) => <option key={status}>{status}</option>)}</select></label>
      <label>Format<select value={query.filters.output_format} onChange={(e) => { query.setFilters({ ...query.filters, output_format: e.target.value }); query.setPage(1); }}><option value="">All formats</option><option value="pdf">PDF</option><option value="json">JSON</option></select></label>
      <label>From<input type="date" value={query.filters.created_from} onChange={(e) => { query.setFilters({ ...query.filters, created_from: e.target.value }); query.setPage(1); }}/></label>
      <label>To<input type="date" value={query.filters.created_to} onChange={(e) => { query.setFilters({ ...query.filters, created_to: e.target.value }); query.setPage(1); }}/></label>
    </SearchFilterBar>
    <section className="ir-panel"><div className="ir-panel__heading"><div><h2>Report Library</h2><p>Generated reports retain an immutable snapshot of selected source data.</p></div></div>{data.error ? <ErrorState message={data.error} onRetry={data.refresh}/> : data.loading ? <div className="ir-state" role="status">Loading reports…</div> : data.items.length ? <ReportTable items={data.items} canManage={canManage} canEditDraft={canEditDraft} canArchive={access.canArchiveReports} onView={openDetails} onPreview={(item) => openDetails(item, "preview")} onEdit={openEdit} onGenerate={(item) => { setSelected(item); setConfirmAction("generate"); }} onDownload={(item) => performAction("download", item)} onDuplicate={(item) => performAction("duplicate", item)} onArchive={(item) => { setSelected(item); setConfirmAction("archive"); }}/> : <div className="ir-state"><FilePlus2 size={24}/><strong>{query.search || query.activeFilterCount ? "No reports match these filters" : "No reports yet"}</strong><span>{canManage ? "Create a draft and preview its selected source records." : "Reports will appear here when available."}</span>{canManage && <button className="ir-button ir-button--primary" onClick={openCreate}><FilePlus2 size={16}/> Create Report</button>}</div>}</section>
    <Pagination page={query.page} pageSize={PAGE_SIZE} total={data.total} loading={data.loading} error={Boolean(data.error)} onPage={query.setPage}/>
    
    <ReportForm open={formOpen} value={form} detections={data.detections} onChange={setForm} onClose={requestCloseForm} onSubmit={submitDraft} onPreview={previewDraft} onGenerate={generateReport} saving={saving} previewing={previewing} error={actionError} editing={Boolean(selected?.id && selected.status === "draft")}/>
    <ConfirmDialog open={discardForm} title="Discard unsaved report?" message="Your report form changes will be lost." confirmLabel="Discard Changes" onCancel={() => setDiscardForm(false)} onConfirm={() => { setDiscardForm(false); setFormOpen(false); }}/>
    <ReportDetailsDrawer open={detailsOpen} report={selected} loading={detailsLoading} error={detailsError || actionError} audit={audit} activeTab={detailsTab} onTab={setDetailsTab} onClose={() => setDetailsOpen(false)} canManage={canManage} canEditDraft={canEditDraft} canArchive={access.canArchiveReports} canReadAudit={access.canReadAudit} onEdit={() => openEdit(selected)} onGenerate={() => setConfirmAction("generate")} onDownload={() => performAction("download")} onDuplicate={() => performAction("duplicate")} onArchive={() => setConfirmAction("archive")} onOpenPage/>
    <DetailsDrawer open={previewOpen} title="Draft Report Preview" description="Preview assembled by the backend from persisted investigation records." onClose={() => setPreviewOpen(false)} loading={previewing} error={previewError} wide footer={<><button type="button" className="ir-button ir-button--secondary" disabled={saving} onClick={() => setPreviewOpen(false)}>Back to Edit</button><button type="button" className="ir-button ir-button--secondary" disabled={saving || !form.detection_ids.length || !form.sections.length} onClick={saveDraft}>{saving ? "Saving…" : "Save Draft"}</button><button type="button" className="ir-button ir-button--primary" disabled={saving || !form.detection_ids.length || !form.sections.length} onClick={generateReport}>{saving ? "Generating…" : "Generate Report"}</button></>}><ReportPreview snapshot={preview} report={form}/></DetailsDrawer>
    {confirmAction === "generate" ? <ReportGenerationDialog open report={selected} busy={saving} onCancel={() => setConfirmAction("")} onConfirm={() => performAction("generate")}/> : <ConfirmDialog open={confirmAction === "archive"} title="Archive report?" message={`Archive “${selected?.title || "this report"}”? It will remain available in archived reports.`} confirmLabel="Archive Report" busy={saving} onCancel={() => setConfirmAction("")} onConfirm={() => performAction("archive")}/>}
    {actionError && !formOpen && !detailsOpen && <div className="ir-alert" role="alert">{actionError}</div>}
  </main>;
}
