import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { Play, RefreshCw } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import ExperimentStatusBadge from "../components/ExperimentStatusBadge";
import ExperimentRunList from "../components/ExperimentRunList";
import ExperimentDetails from "../components/ExperimentDetails";
import useExperimentDetails from "../hooks/useExperimentDetails";
import { experimentsService } from "../services/experimentsService";
import { errorText, formatDate } from "../types";

export default function ExperimentDetailsPage() {
  const { experimentId } = useParams(); const { user } = useAuth(); const location = useLocation(); const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);
  const { experiment: item, loading, error, refresh: load } = useExperimentDetails(experimentId); const [busy, setBusy] = useState(false); const [actionError, setActionError] = useState("");
  async function run() { setBusy(true); setActionError(""); try { const result = await experimentsService.startRun(experimentId); window.location.assign(`/experiments/${experimentId}/runs/${result.id}`); } catch (e) { setActionError(errorText(e)); } finally { setBusy(false); } }
  if (loading && !item) return <main className="ex-page"><div className="ex-state">Loading experiment…</div></main>;
  if (error && !item) return <main className="ex-page"><div className="ex-state ex-state--error"><strong>Experiment details unavailable</strong><span>{error}</span><Link to="/experiments">Back to experiments</Link></div></main>;
  return <main className="ex-page"><header className="ex-page-header"><div><span className="ex-eyebrow">EXPERIMENT / {item.code}</span><h1>{item.name}</h1><p>{item.description || "No description provided."}</p></div><div className="ex-header-actions"><Link className="ex-button ex-button--secondary" to="/experiments">Back to Experiments</Link><button className="ex-button ex-button--secondary" onClick={load} disabled={loading}><RefreshCw size={15}/> Refresh</button>{canManage && <button className="ex-button ex-button--primary" onClick={run} disabled={busy || ["queued", "running"].includes(item.status)}><Play size={15}/>{busy ? "Starting…" : "Run Again"}</button>}</div></header>
    {location.state?.notice && <div className="ex-inline-error" role="status">{location.state.notice}</div>}{actionError && <div className="ex-inline-error">{actionError}</div>}
    <section className="ex-detail-grid"><article><span>Status</span><ExperimentStatusBadge status={item.status}/></article><article><span>Model</span><strong>{item.model_name} · {item.algorithm}</strong></article><article><span>Dataset</span><strong>{item.dataset_name} · v{item.dataset_version_number} · {item.dataset_version_name}</strong></article><article><span>Preprocessing Run</span><code>{item.preprocessing_run_id}</code></article><article><span>Evaluation Split</span><strong>{item.evaluation_split}</strong></article><article><span>Created</span><strong>{formatDate(item.created_at)}</strong></article></section>
    <ExperimentDetails item={item}/>
    <section className="ex-panel"><div className="ex-panel-heading"><div><h2>Experiment Runs</h2><p>Training and evaluation execute through ML Model Management.</p></div></div><ExperimentRunList items={item.runs || []} experimentId={experimentId}/></section>
  </main>;
}
