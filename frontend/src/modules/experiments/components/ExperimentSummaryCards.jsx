const cards = [["TOTAL EXPERIMENTS", "total"], ["COMPLETED", "completed"], ["RUNNING", "running"], ["FAILED", "failed"]];
export default function ExperimentSummaryCards({ summary, loading }) {
  return <section className="ex-summary-grid" aria-label="Experiment statistics">{cards.map(([label, key]) => <article className="ex-summary-card" key={key}><span className="ex-summary-label">{label}</span><strong>{loading ? "…" : Number(summary?.[key] || 0).toLocaleString()}</strong></article>)}</section>;
}
