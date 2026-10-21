import { formatMetric } from "../types";

const metricNames = [["Precision", "precision"], ["Recall", "recall"], ["F1 Score", "f1_score"], ["Accuracy", "accuracy"]];

export default function DetectionPerformance({ data }) {
  const result = data?.evaluation;
  return <section className="an-panel"><header className="an-panel-heading"><div><h2>Detection Performance</h2><p>Most recent completed {data?.evaluation_split || "validation"} evaluation in the selected range</p></div></header>{result ? <><div className="an-performance-grid">{metricNames.map(([label, key]) => <article key={key}><span>{label}</span><strong>{formatMetric(result[key], 2)}</strong></article>)}</div><footer className="an-data-note">{result.model_name} · {result.algorithm} · v{result.version} · {Number(result.sample_count || 0).toLocaleString()} samples</footer></> : <div className="an-empty">No completed {data?.evaluation_split || "validation"} evaluation is available for these filters.</div>}</section>;
}
