import { RotateCcw, Search } from "lucide-react";

export default function ExperimentFilters({ filters, models, datasets, update, reset, loading }) {
  const hasFilters = Object.entries(filters).some(([key, value]) => key !== "sort" && value);
  return <section className="ex-filters"><div className="ex-filter-grid">
    <label className="ex-search"><span>Search</span><div><Search size={15}/><input value={filters.search} placeholder="Experiment name or ID" onChange={(e) => update("search", e.target.value)}/></div></label>
    <label>Status<select value={filters.status} onChange={(e) => update("status", e.target.value)}><option value="">All statuses</option>{["queued", "running", "completed", "failed", "cancelled", "draft"].map((s) => <option value={s} key={s}>{s[0].toUpperCase() + s.slice(1)}</option>)}</select></label>
    <label>Model<select value={filters.model_definition_id} onChange={(e) => update("model_definition_id", e.target.value)}><option value="">All models</option>{models.map((m) => <option key={m.id} value={m.id}>{m.name} · {m.algorithm}</option>)}</select></label>
    <label>Dataset<select value={filters.dataset_version_id} onChange={(e) => update("dataset_version_id", e.target.value)}><option value="">All datasets</option>{datasets.map((d) => <option key={d.dataset_version_id} value={d.dataset_version_id}>{d.dataset_name} · v{d.dataset_version_number} · {d.dataset_version_name}</option>)}</select></label>
    <label>From<input type="date" value={filters.from_date} max={filters.to_date || undefined} onChange={(e) => update("from_date", e.target.value)}/></label>
    <label>To<input type="date" value={filters.to_date} min={filters.from_date || undefined} onChange={(e) => update("to_date", e.target.value)}/></label>
    <label>Sort By<select value={filters.sort} onChange={(e) => update("sort", e.target.value)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="name">Name</option><option value="f1_score">F1 Score</option></select></label>
  </div><div className="ex-filter-actions"><span>{loading ? "Updating experiment list…" : "Filters update the list automatically."}</span><button className="ex-button ex-button--quiet" type="button" onClick={reset} disabled={!hasFilters || loading}><RotateCcw size={15}/> Reset Filters</button></div></section>;
}
