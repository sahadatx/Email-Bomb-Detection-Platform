import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, ArrowLeft, Play } from "lucide-react";
import { experimentsService } from "../services/experimentsService";
import { errorText } from "../types";

export default function ExperimentForm({ inDrawer = false, onClose }) {
  const navigate = useNavigate();
  const [options, setOptions] = useState({ models: [], preprocessing_runs: [] });
  const [name, setName] = useState(""); const [description, setDescription] = useState("");
  const [modelId, setModelId] = useState(""); const [datasetVersionId, setDatasetVersionId] = useState(""); const [preprocessingId, setPreprocessingId] = useState("");
  const [features, setFeatures] = useState([]); const [randomState, setRandomState] = useState("42"); const [hyperparameters, setHyperparameters] = useState("{}"); const [evaluationSplit, setEvaluationSplit] = useState("validation");
  const [loading, setLoading] = useState(true); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  useEffect(() => { experimentsService.options().then((data) => setOptions({ models: data.models || [], preprocessing_runs: data.preprocessing_runs || [] })).catch((e) => setError(errorText(e))).finally(() => setLoading(false)); }, []);
  const datasets = useMemo(() => [...new Map(options.preprocessing_runs.map((row) => [row.dataset_version_id, row])).values()], [options.preprocessing_runs]);
  const prepOptions = options.preprocessing_runs.filter((row) => !datasetVersionId || row.dataset_version_id === datasetVersionId);
  const selectedPrep = options.preprocessing_runs.find((row) => row.preprocessing_run_id === preprocessingId);
  useEffect(() => {
    if (!selectedPrep) { setFeatures([]); return; }
    setFeatures(selectedPrep.features || []);
  }, [preprocessingId]);
  async function submit(event) {
    event.preventDefault(); if (busy) return;
    setBusy(true); setError("");
    let parsed;
    try { parsed = JSON.parse(hyperparameters); if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error(); }
    catch { setError("Hyperparameters must be a valid JSON object."); setBusy(false); return; }
    try {
      const experiment = await experimentsService.create({ name, description: description || null, model_definition_id: modelId, dataset_version_id: datasetVersionId, preprocessing_run_id: preprocessingId, feature_set: features, training_config: { random_state: Number(randomState), hyperparameters: parsed }, evaluation_split: evaluationSplit });
      try {
        const run = await experimentsService.startRun(experiment.id);
        navigate(`/experiments/${experiment.id}/runs/${run.id}`);
      } catch (cause) {
        navigate(`/experiments/${experiment.id}`, { state: { notice: `Experiment saved, but the run could not be started: ${errorText(cause)}` } });
      }
    } catch (cause) { setError(errorText(cause)); setBusy(false); }
  }
  const closeForm = () => inDrawer ? onClose?.() : navigate("/experiments");
  return <main className={inDrawer ? "ex-create-form ex-create-form--drawer" : "ex-page"}>{!inDrawer && <header className="ex-page-header"><div><span className="ex-eyebrow">ANALYTICS / EXPERIMENTS</span><h1>New Experiment</h1><p>Configure an experiment using an active model and a completed preprocessing output.</p></div><button type="button" className="ex-button ex-button--secondary" onClick={closeForm}><ArrowLeft size={15}/> Back to experiments</button></header>}
    <form className="ex-form" onSubmit={submit}><section className="ex-panel"><div className="ex-form-section-heading"><h2>Experiment Definition</h2><p>The saved experiment references the source dataset and model records.</p></div>{error && <div className="ex-inline-error" role="alert"><AlertCircle size={16}/>{error}</div>}
      <div className="ex-form-grid"><label>Experiment Name *<input required minLength={3} maxLength={180} value={name} onChange={(e) => setName(e.target.value)} placeholder="Email Bomb Classifier Baseline"/></label><label className="ex-field-full">Description<textarea maxLength={5000} rows={3} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What are you trying to evaluate?"/></label><label>Model / Algorithm *<select required value={modelId} onChange={(e) => setModelId(e.target.value)}><option value="">Select an active model</option>{options.models.map((model) => <option key={model.id} value={model.id}>{model.name} · {model.algorithm}</option>)}</select></label><label>Dataset Version *<select required value={datasetVersionId} onChange={(e) => { setDatasetVersionId(e.target.value); setPreprocessingId(""); }}><option value="">Select dataset version</option>{datasets.map((row) => <option key={row.dataset_version_id} value={row.dataset_version_id}>{row.dataset_name} · v{row.dataset_version_number} · {row.dataset_version_name}</option>)}</select></label><label className="ex-field-full">Completed Preprocessing Run *<select required value={preprocessingId} onChange={(e) => setPreprocessingId(e.target.value)}><option value="">Select completed preprocessing run</option>{prepOptions.map((row) => <option key={row.preprocessing_run_id} value={row.preprocessing_run_id}>{row.preprocessing_run_id.slice(0, 8)} · {row.feature_count} features · {row.sample_count.toLocaleString()} samples</option>)}</select></label></div>
      {selectedPrep && <div className="ex-source-summary"><strong>{selectedPrep.dataset_name} · v{selectedPrep.dataset_version_number}</strong><span>Train / validation / testing: {selectedPrep.training_count} / {selectedPrep.validation_count} / {selectedPrep.testing_count}</span><span>Choose numeric features; the selected feature subset is used by both training and evaluation.</span></div>}
      <fieldset className="ex-feature-set"><legend>Feature Set *</legend>{selectedPrep?.features?.length ? selectedPrep.features.map((feature) => <label key={feature}><input type="checkbox" checked={features.includes(feature)} onChange={(e) => setFeatures((current) => e.target.checked ? [...current, feature] : current.filter((value) => value !== feature))}/>{feature}</label>) : <p>{preprocessingId ? "This preprocessing run has no numeric feature metadata." : "Choose a preprocessing run to load its supported features."}</p>}</fieldset>
    </section>
    <section className="ex-panel"><div className="ex-form-section-heading"><h2>Training Configuration</h2><p>ML Model Management validates the selected algorithm and parameter values.</p></div><div className="ex-form-grid"><label>Random State<input type="number" step="1" required value={randomState} onChange={(e) => setRandomState(e.target.value)}/></label><label>Evaluation Split<select value={evaluationSplit} onChange={(e) => setEvaluationSplit(e.target.value)}><option value="validation">Validation (model comparison)</option><option value="testing">Testing (final check)</option></select></label><label className="ex-field-full">Hyperparameters (JSON)<textarea rows={7} spellCheck={false} value={hyperparameters} onChange={(e) => setHyperparameters(e.target.value)}/><small>Example: {`{"C": 1, "kernel": "rbf"}`}. Leave as an empty object to use model defaults.</small></label></div><div className="ex-form-footer"><button type="button" className="ex-button ex-button--secondary" onClick={closeForm} disabled={busy}>Cancel</button><button type="submit" className="ex-button ex-button--primary" disabled={busy || loading || !modelId || !datasetVersionId || !preprocessingId || !features.length}><Play size={15}/>{busy ? "Starting experiment…" : "Start Experiment"}</button></div></section></form>
  </main>;
}
