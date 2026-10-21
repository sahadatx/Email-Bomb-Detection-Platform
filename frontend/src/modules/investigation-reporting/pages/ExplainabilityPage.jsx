import { useState } from "react";
import { Link } from "react-router-dom";
import { BrainCircuit, Eye } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import InvestigationPageHeader from "../components/common/InvestigationPageHeader";
import SearchFilterBar from "../components/common/SearchFilterBar";
import Pagination from "../components/common/Pagination";
import ErrorState from "../components/common/ErrorState";
import StatusBadge from "../components/common/StatusBadge";
import ConfirmDialog from "../components/common/ConfirmDialog";
import ExplanationDetailsDrawer from "../components/explainability/ExplanationDetailsDrawer";
import AnalystNoteForm from "../components/explainability/AnalystNoteForm";
import useInvestigationQuery from "../hooks/useInvestigationQuery";
import useExplainability from "../hooks/useExplainability";
import { explainabilityService } from "../services/explainabilityService";
import { investigationError } from "../types";
import { getInvestigationAccess } from "../permissions";

const DEFAULT_FILTERS = { prediction: "", risk_level: "", from_date: "", to_date: "" };
const EMPTY_NOTE = { title: "", body: "", category: "observation" };
const dateTime = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return { date: date.toLocaleDateString(), time: date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) };
};

export default function ExplainabilityPage() {
  const { user } = useAuth();
  const access = getInvestigationAccess(user);
  const isAdmin = access.isAdmin;
  const canAddNote = access.canManage;
  const query = useInvestigationQuery(DEFAULT_FILTERS);
  const data = useExplainability(query);
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [noteOpen, setNoteOpen] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [note, setNote] = useState(EMPTY_NOTE);
  const [deleteNote, setDeleteNote] = useState(null);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState("");
  const [toast, setToast] = useState("");

  async function openDetails(id) {
    setSelectedId(id); setDetail(null); setDetailError(""); setDetailLoading(true);
    try { setDetail(await explainabilityService.detail(id)); }
    catch (error) { setDetailError(investigationError(error)); }
    finally { setDetailLoading(false); }
  }
  function startNote(existing = null) { setEditingNote(existing); setNote(existing ? { title: existing.title || "", body: existing.body, category: existing.category } : EMPTY_NOTE); setActionError(""); setNoteOpen(true); }
  async function saveNote(event) {
    event.preventDefault(); if (!selectedId || saving) return;
    setSaving(true); setActionError("");
    try {
      if (editingNote) await explainabilityService.updateNote(editingNote.id, note);
      else await explainabilityService.addNote(selectedId, note);
      setNoteOpen(false); setToast(editingNote ? "Analyst note updated." : "Analyst note added."); await openDetails(selectedId);
    } catch (error) { setActionError(investigationError(error)); }
    finally { setSaving(false); }
  }
  async function removeNote() {
    if (!deleteNote || saving) return;
    setSaving(true); setActionError("");
    try { await explainabilityService.deleteNote(deleteNote.id); setDeleteNote(null); setToast("Analyst note deleted."); await openDetails(selectedId); }
    catch (error) { setActionError(investigationError(error)); }
    finally { setSaving(false); }
  }
  async function exportDetail() {
    try { await explainabilityService.export(selectedId); }
    catch (error) { setDetailError(investigationError(error)); }
  }

  return <main className="ir-page">
    <InvestigationPageHeader title="Explainability" description="Understand how stored model, risk and behavioral data contributed to each detection." onRefresh={data.refresh} loading={data.loading} actions={<Link className="ir-button ir-button--primary" to="/detection/history">Open Detection History</Link>}/>
    {toast && <div className="ir-notice ir-notice--success" role="status">{toast}<button onClick={() => setToast("")}>Dismiss</button></div>}
    <SearchFilterBar className="ir-explainability-filters" search={query.search} onSearch={query.setSearch} placeholder="Search detection ID, prediction, sender, or model…" onReset={query.reset} showApply={false} count={data.total}>
      <label>Risk Level<select value={query.filters.risk_level} onChange={(e) => { query.setFilters({ ...query.filters, risk_level: e.target.value }); query.setPage(1); }}><option value="">All risk levels</option>{["critical", "high", "medium", "low", "unavailable"].map((value) => <option key={value}>{value}</option>)}</select></label>
      <label>Prediction<select value={query.filters.prediction} onChange={(e) => { query.setFilters({ ...query.filters, prediction: e.target.value }); query.setPage(1); }}><option value="">All predictions</option><option value="bomb">Bomb</option><option value="normal">Normal</option></select></label>
      <label>From<input type="date" value={query.filters.from_date} onChange={(e) => { query.setFilters({ ...query.filters, from_date: e.target.value }); query.setPage(1); }}/></label>
      <label>To<input type="date" value={query.filters.to_date} onChange={(e) => { query.setFilters({ ...query.filters, to_date: e.target.value }); query.setPage(1); }}/></label>
    </SearchFilterBar>
    <section className="ir-panel"><div className="ir-panel__heading"><div><h2>Detection Explanations</h2><p>Attribution is calculated only when the exact registered model and its preprocessing artifacts are available.</p></div></div>
      {data.error ? <ErrorState message={data.error} onRetry={data.refresh}/> : data.loading ? <div className="ir-state" role="status">Loading explanation records…</div> : data.items.length === 0 ? <div className="ir-state"><BrainCircuit size={25}/><strong>{query.search || query.activeFilterCount ? "No matching explanations" : "No detections to explain"}</strong><span>Stored inference results from Detection appear here.</span>{!query.search && !query.activeFilterCount && <Link to="/detection/history">Open Detection History</Link>}</div> : <div className="ir-table-wrap"><table className="ir-table ir-table--email"><thead><tr><th>Detection ID</th><th>Prediction</th><th>Confidence</th><th>Risk</th><th>Model Version</th><th>Detected At</th><th>Action</th></tr></thead><tbody>{data.items.map((row) => { const detectedAt = dateTime(row.created_at); return <tr key={row.id}><td><button className="ir-link-button ir-detection-id" title={String(row.id)} onClick={() => openDetails(row.id)}>{String(row.id)}</button><small>{row.sender || row.email_subject || row.email_id || "Uploaded email"}</small></td><td><StatusBadge status={row.predicted_label}/></td><td>{row.confidence == null ? "—" : `${(row.confidence * 100).toFixed(1)}%`}</td><td>{row.risk?.score == null ? <span className="ir-muted">Unavailable</span> : <span className="ir-risk-cell"><span>{row.risk.score}/100</span><StatusBadge status={row.risk.level}/></span>}</td><td>{row.model_name || "—"}{row.version ? ` · v${row.version}` : ""}</td><td>{detectedAt ? <span className="ir-detected-at"><span>{detectedAt.date}</span><span>{detectedAt.time}</span></span> : "—"}</td><td><button className="ir-button ir-button--small ir-view-button" aria-label={`View explanation for detection ${row.id}`} onClick={() => openDetails(row.id)}><Eye size={15}/> View</button></td></tr>;})}</tbody></table></div>}
      </section>
    <Pagination page={query.page} pageSize={query.pageSize} total={data.total} loading={data.loading} error={Boolean(data.error)} onPage={query.setPage}/>
    
    <ExplanationDetailsDrawer open={Boolean(selectedId)} detection={detail} loading={detailLoading} error={detailError} onClose={() => { setSelectedId(""); setDetail(null); }} notes={detail?.analyst_notes} userId={user?.id} isAdmin={isAdmin} canAddNote={canAddNote} canExport={access.canManage} onAddNote={() => startNote()} onEditNote={startNote} onDeleteNote={setDeleteNote}/>
    <AnalystNoteForm open={noteOpen} value={note} onChange={setNote} onClose={() => setNoteOpen(false)} onSubmit={saveNote} saving={saving} error={actionError} editing={Boolean(editingNote)}/>
    <ConfirmDialog open={Boolean(deleteNote)} title="Delete analyst note?" message="The note will be removed. Its deletion remains in the note audit history." confirmLabel="Delete Note" busy={saving} onCancel={() => setDeleteNote(null)} onConfirm={removeNote}/>
  </main>;
}
