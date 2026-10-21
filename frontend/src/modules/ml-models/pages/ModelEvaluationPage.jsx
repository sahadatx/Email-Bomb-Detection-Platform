import { useCallback, useEffect, useMemo, useState } from "react";
import { Eye } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import { useSearchParams } from "react-router-dom";
import { createEvaluationRun, exportEvaluationReport, getEvaluationRunById, getEvaluationRuns } from "../services/evaluationService";
import { getVersions, getVersionById } from "../services/modelRegistryService";
import { getPreprocessingRun, getTrainingRunById, getTrainingRuns } from "../services/trainingRunService";
import { modelService } from "../services/modelService";
import EvaluationMetrics from "../components/EvaluationMetrics";
import ConfusionMatrix from "../components/ConfusionMatrix";
import ClassificationReport from "../components/ClassificationReport";
import ModelPagination from "../components/ModelPagination";
import "../styles/ml-models.css";

const msg = (e) => e?.response?.data?.detail?.message || e?.response?.data?.detail || e?.message || "Request failed.";
const date = (v) => v ? new Date(v).toLocaleString() : "—";
const PAGE_SIZE = 30;

export default function ModelEvaluationPage() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST"].includes(user?.role);
  const canViewModelData = user?.role !== "EMAIL_ANALYST";
  const [searchParams, setSearchParams] = useSearchParams();
  const [runs, setRuns] = useState([]); const [total, setTotal] = useState(0); const [completedRuns, setCompletedRuns] = useState([]); const [versions, setVersions] = useState([]); const [models, setModels] = useState([]);
  const [page, setPage] = useState(1);
  const [summary, setSummary] = useState({ total: 0, completed: 0, pending: 0, failed: 0 });
  const [search, setSearch] = useState(""); const [status, setStatus] = useState(""); const [split, setSplit] = useState(""); const [modelFilter, setModelFilter] = useState("");
  const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [formError, setFormError] = useState(""); const [toast, setToast] = useState(""); const [busy, setBusy] = useState(false);
  const [drawer, setDrawer] = useState(false); const [selected, setSelected] = useState(null); const [reportBusy, setReportBusy] = useState(false); const [preprocessing, setPreprocessing] = useState(null);
  const [selectedTrainId, setSelectedTrainId] = useState(searchParams.get("training_run_id") || ""); const [selectedSplit, setSelectedSplit] = useState("validation"); const [compareIds, setCompareIds] = useState([]); const [compareOpen, setCompareOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const response = await getEvaluationRuns({ offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, search: search.trim() || undefined, status: status || undefined, evaluation_split: split || undefined, model_definition_id: modelFilter || undefined }); setRuns(response.items || []); setTotal(response.total || 0); }
    catch (e) { setError(msg(e)); setRuns([]); setTotal(0); }
    finally { setLoading(false); }
  }, [search, status, split, modelFilter, page]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    Promise.all([getEvaluationRuns({ offset: 0, limit: 1 }), getEvaluationRuns({ offset: 0, limit: 1, status: "completed" }), getEvaluationRuns({ offset: 0, limit: 1, status: "pending" }), getEvaluationRuns({ offset: 0, limit: 1, status: "failed" })])
      .then(([all, completed, pending, failed]) => setSummary({ total: all.total || 0, completed: completed.total || 0, pending: pending.total || 0, failed: failed.total || 0 }))
      .catch((e) => setFormError(msg(e)));
    if (canViewModelData) getVersions({ offset: 0, limit: 200 }).then((response) => setVersions(response.items || [])).catch(() => {});
    if (canManage) getTrainingRuns({ status: "completed", offset: 0, limit: 200 }).then((response) => setCompletedRuns(response.items || [])).catch(() => {});
  }, [canManage, canViewModelData]);
  const modelMap = useMemo(() => Object.fromEntries(models.map((m) => [m.id, m])), [models]);
  useEffect(() => { if (canViewModelData) modelService.getModels({ offset: 0, limit: 200 }).then((m) => setModels(Array.isArray(m) ? m : m.items || [])).catch(() => {}); }, [canViewModelData]);
  const versionByRun = useMemo(() => Object.fromEntries(versions.map((v) => [v.training_run_id, v])), [versions]);
  const trainById = useMemo(() => Object.fromEntries(completedRuns.map((r) => [r.id, r])), [completedRuns]);
  const eligibleRuns = useMemo(() => completedRuns.filter((r) => versionByRun[r.id]), [completedRuns, versionByRun]);
  const selectedRun = trainById[selectedTrainId]; const selectedVersion = selectedRun && versionByRun[selectedRun.id];

  useEffect(() => { const id = searchParams.get("evaluation_id"); if (id) openReport({ id }); }, []);
  useEffect(() => {
    const versionId = searchParams.get("model_version_id"); const preprocessingId = searchParams.get("preprocessing_run_id");
    if (searchParams.get("training_run_id") && versionId) { setSelectedTrainId(searchParams.get("training_run_id")); setDrawer(true); }
    if (preprocessingId) getPreprocessingRun(preprocessingId).then(setPreprocessing).catch(() => {});
  }, []);
  const submit = async (event) => {
    event.preventDefault(); setFormError("");
    if (!selectedRun || !selectedVersion) { setFormError("Choose a completed training run with a registered model version."); return; }
    if (selectedSplit === "validation" && !(selectedRun.validation_sample_count > 0)) { setFormError("The selected training run has no validation samples."); return; }
    if (selectedSplit === "testing" && !(preprocessing?.testing_count > 0)) { setFormError("Test split metadata is unavailable for this run. Select a run with a processed test split."); return; }
    setBusy(true);
    try { const created = await createEvaluationRun({ model_version_id: selectedVersion.id, preprocessing_run_id: selectedRun.preprocessing_run_id, evaluation_split: selectedSplit }); setDrawer(false); setSelected(created); setToast(`${selectedSplit === "validation" ? "Validation" : "Testing"} evaluation scheduled.`); await load(); }
    catch (e) { setFormError(msg(e)); }
    finally { setBusy(false); }
  };
  async function openReport(row) {
    setSelected(row); setReportBusy(true); setFormError(""); setDrawer(false);
    try {
      const full = await getEvaluationRunById(row.id); setSelected(full);
      const [versionResult, prepResult] = await Promise.allSettled([getVersionById(full.model_version_id), getPreprocessingRun(full.preprocessing_run_id)]);
      if (versionResult.status === "fulfilled") setVersions((current) => [versionResult.value, ...current.filter((v) => v.id !== versionResult.value.id)]);
      if (prepResult.status === "fulfilled") setPreprocessing(prepResult.value);
      setDrawer(true);
    }
    catch (e) { setFormError(msg(e)); setDrawer(true); }
    finally { setReportBusy(false); }
  }
  useEffect(() => {
    let active = true;
    if (!drawer || !selected?.id || !["pending", "running"].includes(selected.status)) return undefined;
    const timer = window.setInterval(() => getEvaluationRunById(selected.id).then((fresh) => { if (active) { setSelected(fresh); load(); } }).catch(() => {}), 4000);
    return () => { active = false; window.clearInterval(timer); };
  }, [drawer, selected?.id, selected?.status, load]);
  const startDrawer = () => { setSelected(null); setSelectedTrainId(searchParams.get("training_run_id") || ""); setSelectedSplit("validation"); setPreprocessing(null); setFormError(""); setDrawer(true); };
  const toggleCompare = (id) => setCompareIds((current) => current.includes(id) ? current.filter((x) => x !== id) : [...current, id]);
  const compareRows = runs.filter((r) => compareIds.includes(r.id));
  const hasFilters = Boolean(search || status || split || modelFilter);
  const resetFilters = () => { setPage(1); setSearch(""); setStatus(""); setSplit(""); setModelFilter(""); };
  const openTrain = (id) => window.location.assign(`/ml-models/training-runs?run_id=${encodeURIComponent(id)}`);
  const exportReport = async (id) => { setFormError(""); try { await exportEvaluationReport(id); } catch (e) { setFormError(msg(e)); } };

  return <main className="ml-page ml-evaluation-page"><header className="ml-page-header"><div><h1>Model Evaluation</h1><p>Evaluate trained models and inspect backend-generated reports.</p></div><div className="ml-page-header__actions"><button className="ml-button ml-button--secondary" onClick={load} disabled={loading}>Refresh</button>{canManage && <button className="ml-button ml-button--primary" onClick={startDrawer}>New Evaluation</button>}</div></header>
    <section className="ml-summary-grid">{[["Total Evaluations", summary.total], ["Completed", summary.completed], ["Pending", summary.pending], ["Failed", summary.failed]].map(([label,value]) => <article className="ml-summary-card" key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>
    {error && <div className="ml-inline-error" role="alert">{error} <button className="ml-button ml-button--small" onClick={load}>Retry</button></div>}
    <section className="ml-panel"><div className="ml-panel__header"><div><h2>Evaluation History</h2><p>Metrics are returned by the evaluation engine.</p></div><button className="ml-button ml-button--secondary" disabled={compareIds.length < 2} onClick={() => setCompareOpen(true)}>Compare selected ({compareIds.length})</button></div>
      <div className="ml-toolbar"><input aria-label="Search evaluations" placeholder="Search evaluation, model, or run..." value={search} onChange={(e) => { setPage(1); setSearch(e.target.value); }} /><select value={status} onChange={(e) => { setPage(1); setStatus(e.target.value); }} aria-label="Filter by status"><option value="">All statuses</option>{["pending", "running", "completed", "failed", "cancelled"].map((s) => <option key={s}>{s}</option>)}</select><select value={split} onChange={(e) => { setPage(1); setSplit(e.target.value); }} aria-label="Filter by split"><option value="">All splits</option><option value="validation">Validation</option><option value="testing">Testing</option></select><select value={modelFilter} onChange={(e) => { setPage(1); setModelFilter(e.target.value); }} aria-label="Filter by model"><option value="">All models</option>{models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select></div><div className="ml-filter-actions"><span>{hasFilters ? "Filters applied to evaluation history." : "Filter evaluation history."}</span><button className="ml-button ml-button--secondary" type="button" disabled={!hasFilters} onClick={resetFilters}>Reset Filters</button></div>
      {!loading && !error && !runs.length ? <div className="ml-empty-state">{search || status || split || modelFilter ? "No evaluations match these filters." : "No evaluations yet. Start one from a completed training run."}</div> : <div className="ml-table-scroll"><table className="ml-data-table"><thead><tr><th>Select</th><th>Evaluation ID</th><th>Model / Version</th><th>Training Run</th><th>Split</th><th>Status</th><th>Accuracy</th><th>Created</th><th>Actions</th></tr></thead><tbody>{runs.map((r) => { const version = versions.find((v) => v.id === r.model_version_id); const modelName = modelMap[version?.model_definition_id]?.name || version?.model_definition_id || "—"; return <tr key={r.id}><td><input type="checkbox" aria-label={`Compare ${r.id}`} checked={compareIds.includes(r.id)} onChange={() => toggleCompare(r.id)} /></td><td>{r.id}</td><td>{modelName} {version && `· v${version.version}`}</td><td><button className="ml-text-button" onClick={() => openTrain(version?.training_run_id)}>{version?.training_run_id || "—"}</button></td><td><span className={`ml-split-badge ml-split-badge--${r.evaluation_split}`}>{r.evaluation_split === "testing" ? "Testing" : "Validation"}</span></td><td><span className={`ml-version-status ml-version-status--${r.status}`}>{r.status}</span></td><td>{r.accuracy == null ? "—" : `${(r.accuracy * 100).toFixed(2)}%`}</td><td>{date(r.created_at)}</td><td><button className="ml-button ml-button--small ml-button--secondary ml-evaluation-view-button" disabled={reportBusy} onClick={() => openReport(r)}><Eye size={14} aria-hidden="true"/>View</button></td></tr>; })}</tbody></table></div>}
      <ModelPagination page={page} pageSize={PAGE_SIZE} total={total} loading={loading} onPage={setPage} />
    </section>
    {drawer && (selected || canManage) && (
      <div className="ml-drawer-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget && !busy) setDrawer(false); }}>
        <aside className="ml-drawer ml-drawer--details" role="dialog" aria-modal="true">
          <header className="ml-drawer__header"><div><span className="ml-eyebrow">MODEL EVALUATION</span><h2>{selected ? `Report ${selected.id}` : "New Evaluation"}</h2><p>{selected ? "Evaluation result and report details." : "Choose a completed training run and split."}</p></div><button className="ml-icon-button" aria-label="Close drawer" onClick={() => setDrawer(false)}>×</button></header>
          {!selected ? (
            <form className="ml-drawer__form" onSubmit={submit}>
              <div className="ml-drawer__body">
                {formError && <div className="ml-alert ml-alert--error" role="alert">{formError}</div>}
                <div className="ml-form-field"><label>Completed training run <span className="ml-required">*</span></label><select required value={selectedTrainId} onChange={async (e) => { const id = e.target.value; setSelectedTrainId(id); setFormError(""); setPreprocessing(null); const row = trainById[id]; if (row) try { setPreprocessing(await getPreprocessingRun(row.preprocessing_run_id)); } catch (err) { setFormError(msg(err)); } }}><option value="">Select training run</option>{eligibleRuns.map((r) => <option key={r.id} value={r.id}>{modelMap[r.model_definition_id]?.name || r.model_definition_id} · {r.id.slice(0, 8)}</option>)}</select></div>
                {selectedRun && selectedVersion && <div className="ml-selection-summary"><strong>{modelMap[selectedRun.model_definition_id]?.name || selectedRun.model_definition_id} · v{selectedVersion.version}</strong><span>Training Run: {selectedRun.id}</span><span>Preprocessing Run: {selectedRun.preprocessing_run_id}</span><span>Dataset: {preprocessing?.dataset_name || "—"} · Version {preprocessing?.dataset_version_number ?? "—"}</span><span>Validation / Testing samples: {selectedRun.validation_sample_count ?? preprocessing?.validation_count ?? "—"} / {preprocessing?.testing_count ?? "—"}</span></div>}
                <div className="ml-form-field"><label>Evaluation split <span className="ml-required">*</span></label><select value={selectedSplit} onChange={(e) => setSelectedSplit(e.target.value)}><option value="validation">Validation</option><option value="testing">Testing</option></select></div>
                <p className="ml-form-hint">Use Validation while comparing models. Use Testing for a final check after model selection.</p>
              </div>
              <footer className="ml-drawer__footer"><button type="button" className="ml-button ml-button--secondary" onClick={() => setDrawer(false)} disabled={busy}>Cancel</button><button type="submit" className="ml-button ml-button--primary" disabled={busy || !selectedRun || !selectedVersion}>{busy ? "Scheduling…" : "Run Evaluation"}</button></footer>
            </form>
          ) : (
            <div className="ml-drawer__body">
              {formError && <div className="ml-alert ml-alert--error">{formError}</div>}
              <dl className="ml-details-list">{[["Status", selected.status], ["Model", modelMap[versions.find((v) => v.id === selected.model_version_id)?.model_definition_id]?.name || "—"], ["Model Version", `v${versions.find((v) => v.id === selected.model_version_id)?.version ?? "—"}`], ["Training Run", versions.find((v) => v.id === selected.model_version_id)?.training_run_id || "—"], ["Dataset Version", preprocessing?.dataset_version_name || preprocessing?.dataset_version_id || "—"], ["Split", selected.evaluation_split], ["Preprocessing Run", selected.preprocessing_run_id], ["Sample count", selected.sample_count], ["Started", date(selected.started_at)], ["Completed", date(selected.completed_at)], ["Duration", selected.duration_ms == null ? "—" : `${(selected.duration_ms / 1000).toFixed(2)} sec`]].map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value ?? "—"}</dd></div>)}</dl>
              {selected.status === "completed" && <><EvaluationMetrics evaluation={selected} /><h3>Confusion Matrix</h3><ConfusionMatrix matrix={selected.confusion_matrix} /><h3>Classification Report</h3><ClassificationReport report={selected.classification_report} /></>}
              {selected.error_message && <div className="ml-alert ml-alert--error"><strong>{selected.error_code || "Evaluation failed"}</strong><p>{selected.error_message}</p></div>}
              <div className="ml-drawer__footer ml-drawer__footer--static">{selected.status === "completed" && <button className="ml-button ml-button--primary" onClick={() => exportReport(selected.id)}>Export JSON</button>}<button className="ml-button ml-button--secondary" onClick={() => openTrain(versions.find((v) => v.id === selected.model_version_id)?.training_run_id)}>View Training Run</button><button className="ml-button ml-button--secondary" onClick={async () => { try { setSelected(await getEvaluationRunById(selected.id)); } catch (e) { setFormError(msg(e)); } }}>Refresh</button></div>
            </div>
          )}
        </aside>
      </div>
    )}
    {compareOpen && <div className="ml-drawer-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) setCompareOpen(false); }}><aside className="ml-drawer ml-drawer--details" role="dialog" aria-modal="true"><header className="ml-drawer__header"><div><span className="ml-eyebrow">COMPARISON</span><h2>Evaluation comparison</h2><p>Stored backend metrics shown side by side.</p></div><button className="ml-icon-button" onClick={() => setCompareOpen(false)}>×</button></header><div className="ml-drawer__body"><div className="ml-table-scroll"><table className="ml-data-table"><thead><tr><th>Evaluation</th><th>Split</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th></tr></thead><tbody>{compareRows.map((r) => <tr key={r.id}><td>{r.id}</td><td>{r.evaluation_split}</td>{[r.accuracy,r.precision,r.recall,r.f1_score,r.roc_auc].map((v,i)=><td key={i}>{v == null ? "—" : `${(v*100).toFixed(2)}%`}</td>)}</tr>)}</tbody></table></div></div></aside></div>}
    {toast && <div className="ml-toast" role="status" onAnimationEnd={() => setToast("")}>{toast}</div>}
  </main>;
}
