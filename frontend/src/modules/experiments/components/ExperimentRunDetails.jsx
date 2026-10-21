import ExperimentStatusBadge from "./ExperimentStatusBadge";
import { formatDate, formatPercent } from "../types";

export default function ExperimentRunDetails({ run }) {
  const progress = Math.max(0, Math.min(100, Number(run.training_run?.progress_percent ?? run.progress_percent ?? 0)));
  return <>
    <section className="ex-detail-grid"><article><span>Status</span><ExperimentStatusBadge status={run.status}/></article><article><span>Progress</span><strong>{progress}%</strong><div className="ex-progress ex-progress--large"><i style={{ width: `${progress}%` }}/></div></article><article><span>Training Run</span><code>{run.training_run_id}</code></article><article><span>Evaluation Run</span><code>{run.evaluation_run_id || "Waiting for training"}</code></article><article><span>Created</span><strong>{formatDate(run.created_at)}</strong></article><article><span>Completed</span><strong>{formatDate(run.completed_at)}</strong></article></section>
    {run.error_summary && <div className="ex-inline-error"><strong>Run failed</strong><span>{run.error_summary}</span></div>}
    {run.evaluation && <section className="ex-panel"><div className="ex-panel-heading"><div><h2>Evaluation Results</h2><p>{run.evaluation.split} split · {Number(run.evaluation.sample_count || 0).toLocaleString()} samples</p></div></div><div className="ex-result-grid">{[["Precision", run.evaluation.precision], ["Recall", run.evaluation.recall], ["F1 Score", run.evaluation.f1_score], ["Accuracy", run.evaluation.accuracy]].map(([label, value]) => <article key={label}><span>{label}</span><strong>{formatPercent(value)}</strong></article>)}</div></section>}
  </>;
}
