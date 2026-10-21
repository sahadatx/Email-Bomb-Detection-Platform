import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { createTrainingRun, getCompletedPreprocessingRuns, getPreprocessingRun, getTrainableModels, getTrainingRunById, getTrainingRunModelVersion, getTrainingRunLogs, getTrainingRuns, retryTrainingRun, resumeTrainingRun } from "../services/trainingRunService";
import TrainingRunTable from "../components/TrainingRunTable";
import TrainingProgress from "../components/TrainingProgress";
import ModelPagination from "../components/ModelPagination";
import "../styles/ml-models.css";

const PAGE_SIZE = 30;
const message = (e) => e?.response?.data?.detail?.message || e?.response?.data?.detail || e?.message || "Request failed.";
const fmtDate = (value) => value ? new Date(value).toLocaleString() : "—";

export default function TrainingRunsPage() {
  const [params, setParams] = useSearchParams();
  const [runs, setRuns] = useState([]); const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [summary, setSummary] = useState({ total: 0, completed: 0, pending: 0, failed: 0 });
  const [models, setModels] = useState([]); const [preprocessingRuns, setPreprocessingRuns] = useState([]);
  const [query, setQuery] = useState(params.get("run_id") || ""); const [status, setStatus] = useState(""); const [modelFilter, setModelFilter] = useState(params.get("model_definition_id") || ""); const [datasetVersionFilter, setDatasetVersionFilter] = useState("");
  const [loading, setLoading] = useState(true); const [pageError, setPageError] = useState(""); const [toast, setToast] = useState("");
  const [drawer, setDrawer] = useState(""); const [selectedRun, setSelectedRun] = useState(null); const [selectedPreprocessing, setSelectedPreprocessing] = useState(null); const [registeredVersion, setRegisteredVersion] = useState(null); const [logs, setLogs] = useState([]);
  const [modelId, setModelId] = useState(params.get("model_definition_id") || ""); const [preprocessingId, setPreprocessingId] = useState(""); const [config, setConfig] = useState("{}"); const [formError, setFormError] = useState(""); const [busy, setBusy] = useState(false);

  const loadRuns = useCallback(async (quiet = false) => {
    if (!quiet) { setLoading(true); setPageError(""); }
    try {
      const [response, allRuns, completed, pending, failed] = await Promise.all([
        getTrainingRuns({ offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, search: query.trim() || undefined, status: status || undefined, model_definition_id: modelFilter || undefined, dataset_version_id: datasetVersionFilter || undefined }),
        getTrainingRuns({ offset: 0, limit: 1 }),
        getTrainingRuns({ offset: 0, limit: 1, status: "completed" }),
        getTrainingRuns({ offset: 0, limit: 1, status: "pending" }),
        getTrainingRuns({ offset: 0, limit: 1, status: "failed" }),
      ]);
      setRuns(response.items || []); setTotal(response.total || 0);
      setSummary({ total: allRuns.total || 0, completed: completed.total || 0, pending: pending.total || 0, failed: failed.total || 0 });
    } catch (e) {
      if (!quiet) { setPageError(message(e)); setRuns([]); setTotal(0); }
    }
    finally { if (!quiet) setLoading(false); }
  }, [query, status, modelFilter, datasetVersionFilter, page]);

  useEffect(() => { loadRuns(); }, [loadRuns]);
  // Runs are asynchronous. Keep the table and summary cards in sync even when
  // the details drawer is closed; status/progress always come from the API.
  useEffect(() => {
    if (!runs.some((run) => ["pending", "queued", "running"].includes(run.status))) return undefined;
    const timer = window.setInterval(() => loadRuns(true), 4000);
    return () => window.clearInterval(timer);
  }, [runs, loadRuns]);
  useEffect(() => {
    Promise.all([getTrainableModels(), getCompletedPreprocessingRuns()]).then(([modelRows, prep]) => {
      setModels(Array.isArray(modelRows) ? modelRows : modelRows.items || []); setPreprocessingRuns(prep.items || []);
    }).catch((e) => setPageError(message(e)));
  }, []);

  const modelById = useMemo(() => Object.fromEntries(models.map((m) => [m.id, m])), [models]);
  const preprocessingById = useMemo(() => Object.fromEntries(preprocessingRuns.map((run) => [run.id, run])), [preprocessingRuns]);
  const datasetVersionOptions = useMemo(() => [...new Map(preprocessingRuns.filter((r) => r.dataset_version_id).map((r) => [r.dataset_version_id, { id: r.dataset_version_id, name: `${r.dataset_name || "Dataset"} · v${r.dataset_version_number ?? "—"}` }])).values()], [preprocessingRuns]);
  const hasFilters = Boolean(query || status || modelFilter || datasetVersionFilter);
  const resetFilters = () => { setPage(1); setQuery(""); setStatus(""); setModelFilter(""); setDatasetVersionFilter(""); };
  const selectedModel = modelById[modelId];
  const openCreate = (preset = "") => { setModelId(preset || params.get("model_definition_id") || ""); setPreprocessingId(""); setConfig("{}"); setSelectedPreprocessing(null); setFormError(""); setDrawer("create"); };
  useEffect(() => {
    if (params.get("create") === "1") openCreate(params.get("model_definition_id") || "");
    const runId = params.get("run_id");
    if (runId) openDetails({ id: runId });
    if (params.get("create") === "1" || runId) setParams({}, { replace: true });
  }, []);

  const choosePreprocessing = async (id) => {
    setPreprocessingId(id); setSelectedPreprocessing(null);
    if (!id) return;
    try { setSelectedPreprocessing(await getPreprocessingRun(id)); } catch (e) { setFormError(message(e)); }
  };
  const submitTraining = async (event) => {
    event.preventDefault(); setFormError("");
    let snapshot;
    try { snapshot = JSON.parse(config); if (!snapshot || Array.isArray(snapshot) || typeof snapshot !== "object") throw new Error(); }
    catch { setFormError("Configuration must be a valid JSON object."); return; }
    setBusy(true);
    try {
      const created = await createTrainingRun({ model_definition_id: modelId, preprocessing_run_id: preprocessingId, config_snapshot: snapshot });
      setDrawer("details"); setSelectedRun(created); setToast("Training run queued."); await loadRuns();
    } catch (e) { setFormError(message(e)); }
    finally { setBusy(false); }
  };
  const openDetails = async (run) => {
    setDrawer("details"); setSelectedRun(run); setLogs([]); setSelectedPreprocessing(null); setRegisteredVersion(null);
    try {
      const latest = await getTrainingRunById(run.id);
      setSelectedRun(latest);
      const [logResult, preprocessingResult, versionResult] = await Promise.allSettled([
        getTrainingRunLogs(latest.id), getPreprocessingRun(latest.preprocessing_run_id), getTrainingRunModelVersion(latest.id),
      ]);
      if (logResult.status === "fulfilled") setLogs(logResult.value.items || []);
      if (preprocessingResult.status === "fulfilled") setSelectedPreprocessing(preprocessingResult.value);
      if (versionResult.status === "fulfilled") setRegisteredVersion(versionResult.value);
    }
    catch (e) { setFormError(message(e)); }
  };
  useEffect(() => {
    if (drawer !== "details" || !selectedRun || !["pending", "queued", "running"].includes(selectedRun.status)) return undefined;
    const timer = window.setInterval(async () => {
      try { const fresh = await getTrainingRunById(selectedRun.id); setSelectedRun(fresh); await loadRuns(true); }
      catch { /* Keep the last server response visible. */ }
    }, 4000);
    return () => window.clearInterval(timer);
  }, [drawer, selectedRun?.id, selectedRun?.status, loadRuns]);
  const handleRetry = async () => {
    if (!window.confirm(`Create a new training run using the source and configuration from ${selectedRun.id}?`)) return;
    setBusy(true); setFormError("");
    try { const created = await retryTrainingRun(selectedRun.id); setSelectedRun(created); setToast("Retry run created."); await loadRuns(); }
    catch (e) { setFormError(message(e)); }
    finally { setBusy(false); }
  };
  const handleResume = async (run) => {
    if (!window.confirm(`Start pending training run ${run.id}?`)) return;
    setBusy(true);
    try { await resumeTrainingRun(run.id); setToast("Training run dispatched."); await loadRuns(); }
    catch (e) { setPageError(message(e)); }
    finally { setBusy(false); }
  };
  const evaluate = async () => {
    let version;
    try { version = await getTrainingRunModelVersion(selectedRun.id); }
    catch { setFormError("This completed run has no registered model version yet."); return; }
    window.location.assign(`/ml-models/evaluation?training_run_id=${encodeURIComponent(selectedRun.id)}&model_version_id=${encodeURIComponent(version.id)}&preprocessing_run_id=${encodeURIComponent(selectedRun.preprocessing_run_id)}`);
  };

  return <main className="ml-page ml-training-page">
    <header className="ml-page-header"><div><h1>Training Runs</h1><p>Start and monitor model training.</p></div><div className="ml-page-header__actions"><button className="ml-button ml-button--secondary" onClick={loadRuns} disabled={loading}>Refresh</button><button className="ml-button ml-button--primary" onClick={() => openCreate()}>New Training</button></div></header>
    <section className="ml-summary-grid">{[["Total Runs", summary.total], ["Completed", summary.completed], ["Pending", summary.pending], ["Failed", summary.failed]].map(([label, value]) => <article className="ml-summary-card" key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>
    <section className="ml-panel"><div className="ml-panel__header"><div><h2>Training History</h2><p>Progress and run status are reported by the backend.</p></div><span className="ml-panel__count">{total} runs</span></div>
      <div className="ml-toolbar"><input aria-label="Search training runs" placeholder="Search run ID, model, or preprocessing run..." value={query} onChange={(e) => { setPage(1); setQuery(e.target.value); }} /><select aria-label="Filter by status" value={status} onChange={(e) => { setPage(1); setStatus(e.target.value); }}><option value="">All statuses</option>{["pending", "queued", "running", "completed", "failed", "cancelled"].map((value) => <option key={value} value={value}>{value.charAt(0).toUpperCase() + value.slice(1)}</option>)}</select><select aria-label="Filter by model" value={modelFilter} onChange={(e) => { setPage(1); setModelFilter(e.target.value); }}><option value="">All models</option>{models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select><select aria-label="Filter by dataset version" value={datasetVersionFilter} onChange={(e) => { setPage(1); setDatasetVersionFilter(e.target.value); }}><option value="">All dataset versions</option>{datasetVersionOptions.map((version) => <option key={version.id} value={version.id}>{version.name}</option>)}</select></div>
      <div className="ml-filter-actions"><span>{hasFilters ? "Filters applied to training history." : "Filter training history."}</span><button className="ml-button ml-button--secondary" type="button" disabled={!hasFilters} onClick={resetFilters}>Reset Filters</button></div>
      {pageError && <div className="ml-inline-error" role="alert">{pageError} <button className="ml-button ml-button--small" onClick={loadRuns}>Retry</button></div>}
      {!pageError && !loading && total > 0 && runs.length === 0 && <div className="ml-empty-state">No training runs match these filters.</div>}
      <TrainingRunTable runs={runs.map((run) => ({ ...run, model_name: modelById[run.model_definition_id]?.name || run.model_definition_id, preprocessing: preprocessingById[run.preprocessing_run_id] }))} loading={loading} error={pageError} hasFilters={Boolean(query || status || modelFilter || datasetVersionFilter)} onView={openDetails} onResume={handleResume} onRefresh={loadRuns} />
      <ModelPagination page={page} pageSize={PAGE_SIZE} total={total} loading={loading} onPage={setPage} />
    </section>

    {drawer && <div className="ml-drawer-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget && !busy) setDrawer(""); }}><aside className="ml-drawer ml-drawer--details" role="dialog" aria-modal="true"><header className="ml-drawer__header"><div><span className="ml-eyebrow">TRAINING RUN</span><h2>{drawer === "create" ? "New Training" : selectedRun?.id || "Run details"}</h2><p>{drawer === "create" ? "Select a model and completed preprocessing output." : "Run state and outputs from the backend."}</p></div><button className="ml-icon-button" aria-label="Close drawer" onClick={() => setDrawer("")}>×</button></header>
      {drawer === "create" ? <form className="ml-drawer__form" onSubmit={submitTraining}><div className="ml-drawer__body">{formError && <div className="ml-alert ml-alert--error" role="alert">{formError}</div>}
        <div className="ml-form-field"><label>Model <span className="ml-required">*</span></label><select required value={modelId} onChange={(e) => { setModelId(e.target.value); setConfig("{}"); }}><option value="">Select active model</option>{models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select>{selectedModel && <small>Model defaults: {JSON.stringify(selectedModel.hyperparameters || {})}</small>}</div>
        <div className="ml-form-field"><label>Completed preprocessing run <span className="ml-required">*</span></label><select required value={preprocessingId} onChange={(e) => choosePreprocessing(e.target.value)}><option value="">Select completed run</option>{preprocessingRuns.map((r) => <option key={r.id} value={r.id}>{r.dataset_name || "Dataset"} v{r.dataset_version_number ?? "—"} · {r.id.slice(0, 8)}</option>)}</select></div>
        {selectedPreprocessing && <div className="ml-selection-summary"><strong>{selectedPreprocessing.dataset_name || "Dataset"} · Version {selectedPreprocessing.dataset_version_number ?? "—"}</strong><span>Run {selectedPreprocessing.id}</span><span>Processed rows: {selectedPreprocessing.output_sample_count ?? "—"} · Features: {selectedPreprocessing.feature_count ?? "—"}</span><span>Train / Validation / Test: {selectedPreprocessing.training_count ?? "—"} / {selectedPreprocessing.validation_count ?? "—"} / {selectedPreprocessing.testing_count ?? "—"}</span><span>Artifacts: {selectedPreprocessing.artifacts?.map((a) => a.artifact_type).join(", ") || "No artifact metadata"}</span></div>}
        <div className="ml-form-field"><label>Allowed overrides (JSON)</label><textarea rows={8} spellCheck={false} value={config} onChange={(e) => setConfig(e.target.value)} /><small>Leave empty to use model defaults. Overrides may set hyperparameters and random_state; backend validates all values.</small></div>
      </div><footer className="ml-drawer__footer"><button type="button" className="ml-button ml-button--secondary" onClick={() => setDrawer("")} disabled={busy}>Cancel</button><button type="submit" className="ml-button ml-button--primary" disabled={busy || !modelId || !preprocessingId}>{busy ? "Starting…" : "Start Training"}</button></footer></form> : selectedRun && <div className="ml-drawer__body ml-run-details">
        {formError && <div className="ml-alert ml-alert--error" role="alert">{formError}</div>}<TrainingProgress run={selectedRun} />
        <dl className="ml-details-list">{[["Status", selectedRun.status], ["Progress", `${selectedRun.progress_percent ?? 0}%`], ["Model", modelById[selectedRun.model_definition_id]?.name || selectedRun.model_definition_id], ["Model ID", selectedRun.model_definition_id], ["Model Version", registeredVersion ? `v${registeredVersion.version} · ${registeredVersion.status}` : "Not registered"], ["Dataset", selectedPreprocessing?.dataset_name], ["Dataset Version", selectedPreprocessing?.dataset_version_name || selectedPreprocessing?.dataset_version_id], ["Preprocessing Run", selectedRun.preprocessing_run_id], ["Started", fmtDate(selectedRun.started_at)], ["Completed", fmtDate(selectedRun.completed_at)], ["Duration", selectedRun.duration_ms == null ? "—" : `${(selectedRun.duration_ms / 1000).toFixed(2)} sec`], ["Train samples", selectedRun.training_sample_count], ["Validation samples", selectedRun.validation_sample_count], ["Test samples", selectedPreprocessing?.testing_count]].map(([k,v]) => <div key={k}><dt>{k}</dt><dd>{v ?? "—"}</dd></div>)}</dl>
        {selectedPreprocessing?.artifacts?.length > 0 && <><h3>Processed artifacts</h3><ul className="ml-related-list">{selectedPreprocessing.artifacts.map((artifact) => <li key={artifact.id}>{artifact.artifact_type} · {artifact.filename} · {artifact.size_bytes?.toLocaleString()} bytes</li>)}</ul></>}
        <h3>Configuration snapshot</h3><pre className="ml-json-view">{JSON.stringify(selectedRun.config_snapshot || {}, null, 2)}</pre>
        <h3>Logs</h3>{logs.length ? <ol className="ml-run-logs">{logs.map((line, i) => <li key={`${i}-${line}`}>{typeof line === "string" ? line : JSON.stringify(line)}</li>)}</ol> : <p>No lifecycle logs returned.</p>}
        {selectedRun.error_message && <div className="ml-alert ml-alert--error"><strong>{selectedRun.error_code || "Training failed"}</strong><p>{selectedRun.error_message}</p></div>}
        {selectedRun.result_summary && <><h3>Training summary</h3><pre className="ml-json-view">{JSON.stringify(selectedRun.result_summary, null, 2)}</pre></>}
        <footer className="ml-drawer__footer ml-drawer__footer--static">{selectedRun.status === "failed" && <button className="ml-button ml-button--secondary" onClick={handleRetry} disabled={busy}>{busy ? "Retrying…" : "Retry as new run"}</button>}{selectedRun.status === "completed" && <button className="ml-button ml-button--primary" onClick={evaluate}>Evaluate model</button>}<button className="ml-button ml-button--secondary" onClick={() => window.location.assign(`/ml-models/models?model_id=${encodeURIComponent(selectedRun.model_definition_id)}`)}>View Model</button><button className="ml-button ml-button--secondary" onClick={async () => { try { await openDetails(selectedRun); } catch {} }}>Refresh details</button></footer>
      </div>}</aside></div>}
    {toast && <div className="ml-toast" role="status" onAnimationEnd={() => setToast("")}>{toast}</div>}
  </main>;
}
