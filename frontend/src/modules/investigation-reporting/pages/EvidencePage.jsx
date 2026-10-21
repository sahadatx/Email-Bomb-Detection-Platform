import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ShieldAlert } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import InvestigationPageHeader from "../components/common/InvestigationPageHeader";
import SummaryCards from "../components/common/SummaryCards";
import SearchFilterBar from "../components/common/SearchFilterBar";
import Pagination from "../components/common/Pagination";
import ErrorState from "../components/common/ErrorState";
import ConfirmDialog from "../components/common/ConfirmDialog";
import EvidenceTable from "../components/evidence/EvidenceTable";
import EvidenceForm from "../components/evidence/EvidenceForm";
import EvidenceDetailsDrawer from "../components/evidence/EvidenceDetailsDrawer";
import EvidenceReviewDrawer from "../components/evidence/EvidenceReviewDrawer";
import useInvestigationQuery from "../hooks/useInvestigationQuery";
import useEvidence from "../hooks/useEvidence";
import { evidenceService } from "../services/evidenceService";
import { detectionService } from "../../detection/services/detectionService";
import { EVIDENCE_TYPES, investigationError } from "../types";
import { getInvestigationAccess } from "../permissions";

const DEFAULT_FILTERS = { status: "", evidence_type: "", from_date: "", to_date: "" };
const EMPTY_FORM = { name: "", evidence_type: "", detection_id: "", source_email_id: "", description: "", observed_value: "", provenance_source: "", collected_at: "", analyst_note: "" };
const EMPTY_REVIEW = { review_status: "verified", reason: "", analyst_comment: "" };
const asOptional = (value) => value || undefined;

export default function EvidencePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const access = getInvestigationAccess(user);
  const canManage = access.canManage;
  const query = useInvestigationQuery(DEFAULT_FILTERS);
  const data = useEvidence(query);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formInitial, setFormInitial] = useState(EMPTY_FORM);
  const [emailLinkLoading, setEmailLinkLoading] = useState(false);
  const [discardForm, setDiscardForm] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [review, setReview] = useState(EMPTY_REVIEW);
  const [selected, setSelected] = useState(null);
  const [detailsTab, setDetailsTab] = useState("overview");
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  async function openDetails(record, tab = "overview") {
    setSelected(record); setDetailsTab(tab); setDetail(null); setDetailError(""); setDetailLoading(true);
    try { setDetail(await evidenceService.detail(record.id)); }
    catch (cause) { setDetailError(investigationError(cause)); }
    finally { setDetailLoading(false); }
  }
  function startCreate() { setSelected(null); setEditing(false); setForm(EMPTY_FORM); setFormInitial(EMPTY_FORM); setError(""); setFormOpen(true); }
  function startEdit(record) { const values = { ...EMPTY_FORM, name: record.name, evidence_type: record.evidence_type, detection_id: record.detection_id, source_email_id: record.source_email_id || "", description: record.description || "", observed_value: record.observed_value || "", provenance_source: record.provenance?.source || "", analyst_note: record.analyst_note || "" }; setSelected(record); setEditing(true); setForm(values); setFormInitial(values); setError(""); setFormOpen(true); }
  function requestCloseForm() { if (saving) return; if (JSON.stringify(form) !== JSON.stringify(formInitial)) setDiscardForm(true); else setFormOpen(false); }
  async function selectDetection(detectionId) {
    const row = data.detections.find((item) => String(item.id) === String(detectionId));
    let emailId = row?.email_id || row?.source_email_id || row?.email?.id || "";
    setForm((current) => ({ ...current, detection_id: detectionId, source_email_id: emailId }));
    if (!detectionId || emailId) return;
    setEmailLinkLoading(true);
    try {
      const detail = await detectionService.detail(detectionId);
      emailId = detail?.email_id || detail?.source_email_id || detail?.email?.id || "";
      setForm((current) => current.detection_id === detectionId ? { ...current, source_email_id: emailId } : current);
    } catch (cause) {
      setError(`Could not load the linked email for this detection: ${investigationError(cause)}`);
    } finally {
      setEmailLinkLoading(false);
    }
  }
  async function saveEvidence(event) {
    event.preventDefault(); if (saving) return;
    setSaving(true); setError("");
    const payload = { name: form.name, evidence_type: form.evidence_type, ...(editing ? {} : { detection_id: form.detection_id, collected_at: form.collected_at || undefined }), source_email_id: asOptional(form.source_email_id), description: asOptional(form.description), observed_value: asOptional(form.observed_value), provenance: form.provenance_source ? { source: form.provenance_source } : {}, analyst_note: asOptional(form.analyst_note) };
    try {
      if (editing) await evidenceService.update(selected.id, payload);
      else await evidenceService.create(payload);
      setFormOpen(false); setToast(editing ? "Evidence updated; verified evidence returned to pending review when changed." : "Evidence record created in pending review."); await data.refresh();
    } catch (cause) { setError(investigationError(cause)); }
    finally { setSaving(false); }
  }
  function startReview(record) { setSelected(record); setReview({ ...EMPTY_REVIEW, review_status: record.review_status === "verified" ? "flagged" : "verified" }); setError(""); setReviewOpen(true); }
  async function saveReview(event) {
    event.preventDefault(); if (!selected || saving) return;
    setSaving(true); setError("");
    try { await evidenceService.review(selected.id, review); setReviewOpen(false); setToast("Evidence review decision saved."); await data.refresh(); await openDetails(selected); }
    catch (cause) { setError(investigationError(cause)); }
    finally { setSaving(false); }
  }
  const summary = data.summary || {};

  return <main className="ir-page">
    <InvestigationPageHeader title="Evidence Management" description="Collect, review, validate and preserve evidence linked to stored detections." onRefresh={data.refresh} loading={data.loading} actions={canManage && <button className="ir-button ir-button--primary" onClick={startCreate}><Plus size={16}/> Add Evidence</button>}/>
    {toast && <div className="ir-notice ir-notice--success" role="status">{toast}<button onClick={() => setToast("")}>Dismiss</button></div>}
    <SummaryCards loading={data.loading} items={[["Total Evidence", summary.total], ["Verified", summary.verified], ["Pending Review", summary.pending], ["Flagged", summary.flagged]].map(([label, value]) => ({ label, value }))}/>
    <SearchFilterBar className="ir-evidence-filters" search={query.search} onSearch={query.setSearch} placeholder="Search evidence ID, name, detection, or source…" onReset={query.reset} showApply={false} count={data.total}>
      <label>Evidence Type<select value={query.filters.evidence_type} onChange={(e) => { query.setFilters({ ...query.filters, evidence_type: e.target.value }); query.setPage(1); }}><option value="">All types</option>{EVIDENCE_TYPES.map((type) => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}</select></label>
      <label>Review Status<select value={query.filters.status} onChange={(e) => { query.setFilters({ ...query.filters, status: e.target.value }); query.setPage(1); }}><option value="">All statuses</option>{["pending", "verified", "flagged", "rejected"].map((status) => <option value={status} key={status}>{status}</option>)}</select></label>
      <label>From<input type="date" value={query.filters.from_date} onChange={(e) => { query.setFilters({ ...query.filters, from_date: e.target.value }); query.setPage(1); }}/></label>
      <label>To<input type="date" value={query.filters.to_date} onChange={(e) => { query.setFilters({ ...query.filters, to_date: e.target.value }); query.setPage(1); }}/></label>
    </SearchFilterBar>
    <section className="ir-panel"><div className="ir-panel__heading"><div><h2>Evidence Records</h2><p>Review status describes the evidence workflow, not a threat verdict.</p></div></div>{data.error ? <ErrorState message={data.error} onRetry={data.refresh}/> : data.loading ? <div className="ir-state" role="status">Loading evidence records…</div> : data.items.length ? <EvidenceTable items={data.items} canManage={canManage} onView={openDetails} onEdit={startEdit} onReview={startReview} onAudit={access.canReadAudit ? (record) => openDetails(record, "audit") : undefined} onDetection={(record) => navigate(`/detection/history?detection_id=${record.detection_id}`)}/> : <div className="ir-state"><ShieldAlert size={24}/><strong>{query.search || query.activeFilterCount ? "No evidence matches these filters" : "No evidence records yet"}</strong><span>Evidence records link observations to existing detection records.</span>{canManage && <button className="ir-button ir-button--primary" onClick={startCreate}><Plus size={16}/> Add Evidence</button>}</div>}</section>
    <Pagination page={query.page} pageSize={query.pageSize} total={data.total} loading={data.loading} error={Boolean(data.error)} onPage={query.setPage}/>
    
    <EvidenceForm open={formOpen} value={form} detections={data.detections} onChange={setForm} onDetectionChange={selectDetection} emailLinkLoading={emailLinkLoading} onClose={requestCloseForm} onSubmit={saveEvidence} saving={saving} error={error} editing={editing}/>
    <ConfirmDialog open={discardForm} title="Discard unsaved evidence?" message="Your evidence form changes will be lost." confirmLabel="Discard Changes" onCancel={() => setDiscardForm(false)} onConfirm={() => { setDiscardForm(false); setFormOpen(false); }}/>
    <EvidenceReviewDrawer open={reviewOpen} currentStatus={selected?.review_status} value={review} onChange={setReview} onClose={() => setReviewOpen(false)} onSubmit={saveReview} saving={saving} error={error}/>
    <EvidenceDetailsDrawer open={Boolean(selected && !formOpen && !reviewOpen)} data={detail} loading={detailLoading} error={detailError} activeTab={detailsTab} onClose={() => { setSelected(null); setDetail(null); }} canManage={canManage} canReadAudit={access.canReadAudit} onEdit={() => startEdit(detail?.evidence || selected)} onReview={() => startReview(detail?.evidence || selected)}/>
  </main>;
}
