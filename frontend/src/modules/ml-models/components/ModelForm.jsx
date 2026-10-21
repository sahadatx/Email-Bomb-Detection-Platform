import { useEffect, useState } from "react";
import { LoaderCircle, X } from "lucide-react";
import { ML_MODEL_TYPE } from "../types";
import { getAlgorithmLabel } from "../types";

export default function ModelForm({ open, model = null, algorithms = [], submitting = false, error = "", onClose, onSubmit }) {
  const [name, setName] = useState(""); const [description, setDescription] = useState(""); const [algorithm, setAlgorithm] = useState(""); const [configuration, setConfiguration] = useState("{}"); const [status, setStatus] = useState("active"); const [configError, setConfigError] = useState("");
  const isEditing = Boolean(model);
  useEffect(() => {
    if (!open) return;
    const choice = model?.algorithm || algorithms[0]?.algorithm || "";
    setName(model?.name || ""); setDescription(model?.description || ""); setAlgorithm(choice);
    setConfiguration(JSON.stringify(model?.hyperparameters || algorithms.find((a) => a.algorithm === choice)?.default_hyperparameters || {}, null, 2));
    setStatus(model?.status || "active"); setConfigError("");
  }, [open, model, algorithms]);
  if (!open) return null;
  const submit = (event) => {
    event.preventDefault(); setConfigError("");
    let hyperparameters;
    try { hyperparameters = JSON.parse(configuration); if (!hyperparameters || Array.isArray(hyperparameters) || typeof hyperparameters !== "object") throw new Error(); }
    catch { setConfigError("Configuration must be a valid JSON object."); return; }
    onSubmit?.({ name: name.trim(), description: description.trim() || null, model_type: ML_MODEL_TYPE.CLASSIFIER, algorithm, hyperparameters, ...(!isEditing ? { status } : {}) });
  };
  return <div className="ml-drawer-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget && !submitting) onClose?.(); }}><aside className="ml-drawer" role="dialog" aria-modal="true" aria-labelledby="ml-model-form-title"><header className="ml-drawer__header"><div><span className="ml-eyebrow">MODEL MANAGEMENT</span><h2 id="ml-model-form-title">{isEditing ? "Edit model" : "Create model"}</h2><p>{isEditing ? "Update this model definition." : "Create a definition; training is started separately."}</p></div><button type="button" className="ml-icon-button" aria-label="Close drawer" onClick={onClose} disabled={submitting}><X size={19}/></button></header>
    <form className="ml-drawer__form" onSubmit={submit}><div className="ml-drawer__body">{error && <div className="ml-alert ml-alert--error" role="alert">{error}</div>}
      <div className="ml-form-field"><label htmlFor="ml-model-name">Model name <span className="ml-required">*</span></label><input id="ml-model-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={150} required disabled={submitting} placeholder="e.g. Email Bomb Detector"/></div>
      <div className="ml-form-field"><label htmlFor="ml-model-description">Description</label><textarea id="ml-model-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={4} disabled={submitting} placeholder="Describe the model purpose…"/></div>
      <div className="ml-form-field"><label>Model type</label><input value="Classifier" disabled readOnly/><small>The backend currently supports classifier models only.</small></div>
      <div className="ml-form-field"><label htmlFor="ml-model-algorithm">Algorithm <span className="ml-required">*</span></label><select id="ml-model-algorithm" value={algorithm} onChange={(e) => { const next = e.target.value; setAlgorithm(next); setConfiguration(JSON.stringify(algorithms.find((a) => a.algorithm === next)?.default_hyperparameters || {}, null, 2)); }} required disabled={submitting || algorithms.length === 0}><option value="">Select algorithm</option>{algorithms.map((a) => <option key={a.algorithm} value={a.algorithm}>{getAlgorithmLabel(a.algorithm)}</option>)}</select></div>
      <div className="ml-form-field"><label htmlFor="ml-model-config">Algorithm configuration (JSON)</label><textarea id="ml-model-config" rows={8} spellCheck={false} value={configuration} onChange={(e) => setConfiguration(e.target.value)} disabled={submitting}/><small>Defaults come from the backend algorithms endpoint. The backend validates all values.</small>{configError && <p className="ml-form-error" role="alert">{configError}</p>}</div>
      {!isEditing && <div className="ml-form-field"><label htmlFor="ml-model-status">Initial status</label><select id="ml-model-status" value={status} onChange={(e) => setStatus(e.target.value)} disabled={submitting}><option value="active">Active</option><option value="inactive">Inactive</option></select></div>}
    </div><footer className="ml-drawer__footer"><button type="button" className="ml-button ml-button--secondary" onClick={onClose} disabled={submitting}>Cancel</button><button type="submit" className="ml-button ml-button--primary" disabled={submitting || !name.trim() || !algorithm}>{submitting ? <><LoaderCircle size={16} className="ml-spin"/> Saving…</> : isEditing ? "Save changes" : "Create model"}</button></footer></form></aside></div>;
}
