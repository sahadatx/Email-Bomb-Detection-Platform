import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ExperimentRunDetails from "../components/ExperimentRunDetails";
import ExperimentLogs from "../components/ExperimentLogs";
import { experimentsService } from "../services/experimentsService";
import { errorText, formatDate } from "../types";

export default function ExperimentRunDetailsPage() {
  const { experimentId, runId } = useParams(); const [run, setRun] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(async () => { try { const result = await experimentsService.run(runId); setRun(result); setError(""); } catch (e) { setError(errorText(e)); } finally { setLoading(false); } }, [runId]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (!run || !["queued", "running"].includes(run.status)) return undefined; const timer = window.setInterval(load, 2500); return () => window.clearInterval(timer); }, [run?.status, load]);
  if (loading && !run) return <main className="ex-page"><div className="ex-state">Loading experiment run…</div></main>;
  if (!run) return <main className="ex-page"><div className="ex-state ex-state--error">{error || "Experiment run was not found."}<Link to={`/experiments/${experimentId}`}>Back to experiment</Link></div></main>;
  return <main className="ex-page"><header className="ex-page-header"><div><span className="ex-eyebrow">EXPERIMENT RUN</span><h1>{run.experiment_name}</h1><p>{run.experiment_code} · {run.id}</p></div><div className="ex-header-actions"><Link className="ex-button ex-button--secondary" to={`/experiments/${experimentId}`}>Experiment Details</Link><button className="ex-button ex-button--secondary" onClick={load}>Refresh</button></div></header>
    {error && <div className="ex-inline-error">{error}</div>}
    <ExperimentRunDetails run={run}/>
    <section className="ex-panel"><div className="ex-panel-heading"><div><h2>Run Logs</h2><p>Lifecycle messages from orchestration and source ML tasks.</p></div></div><ExperimentLogs items={run.logs || []}/></section>
  </main>;
}
