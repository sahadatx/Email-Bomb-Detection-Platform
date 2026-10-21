import { Link } from "react-router-dom";
import { formatDate, formatPercent } from "../types";
import ExperimentStatusBadge from "./ExperimentStatusBadge";

export default function ExperimentRunList({ items = [], experimentId }) {
  if (!items.length) return <div className="ex-empty">No runs yet. Start this experiment to train and evaluate the selected configuration.</div>;
  return <div className="ex-table-wrap"><table className="ex-table"><thead><tr><th>Run</th><th>Status</th><th>Progress</th><th>Split</th><th>Accuracy</th><th>F1 Score</th><th>Created</th><th>Action</th></tr></thead><tbody>{items.map((run) => <tr key={run.id}><td><code>{run.id.slice(0, 13)}…</code></td><td><ExperimentStatusBadge status={run.status}/></td><td>{run.progress_percent}%</td><td>{run.evaluation_split || "—"}</td><td>{formatPercent(run.metrics?.accuracy)}</td><td>{formatPercent(run.metrics?.f1_score)}</td><td>{formatDate(run.created_at)}</td><td><Link className="ex-link-action" to={`/experiments/${experimentId}/runs/${run.id}`}>View run</Link></td></tr>)}</tbody></table></div>;
}
