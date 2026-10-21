import { RotateCcw } from "lucide-react";
import { ANALYTICS_RANGES, DEFAULT_ANALYTICS_FILTERS } from "../types";

export default function AnalyticsFilters({ filters, models, update, reset, disabled }) {
  const changed = Object.keys(DEFAULT_ANALYTICS_FILTERS).some((key) => filters[key] !== DEFAULT_ANALYTICS_FILTERS[key]);
  return <section className="an-filters" aria-label="Analytics filters">
    <div className="an-filter-grid">
      <label>From<input type="date" value={filters.from_date} max={filters.to_date || undefined} onChange={(e) => { update("time_range", "custom"); update("from_date", e.target.value); }} disabled={disabled}/></label>
      <label>To<input type="date" value={filters.to_date} min={filters.from_date || undefined} onChange={(e) => { update("time_range", "custom"); update("to_date", e.target.value); }} disabled={disabled}/></label>
      <label>Last<select value={filters.time_range === "custom" ? "custom" : filters.time_range} onChange={(e) => { update("time_range", e.target.value); if (e.target.value !== "custom") { update("from_date", ""); update("to_date", ""); } }} disabled={disabled}>{ANALYTICS_RANGES.map((range) => <option value={range.value} key={range.value}>{range.label}</option>)}</select></label>
      <label>Classification<select value={filters.classification} onChange={(e) => update("classification", e.target.value)} disabled={disabled}><option value="">All classifications</option><option value="normal">Normal</option><option value="bomb">Bomb</option></select></label>
      <label>Risk Level<select value={filters.risk_level} onChange={(e) => update("risk_level", e.target.value)} disabled={disabled}><option value="">All risk levels</option>{["low", "medium", "high", "critical"].map((value) => <option key={value} value={value}>{value[0].toUpperCase() + value.slice(1)}</option>)}</select></label>
      <label>Model<select value={filters.model_definition_id} onChange={(e) => update("model_definition_id", e.target.value)} disabled={disabled}><option value="">All models</option>{models.map((model) => <option key={model.id} value={model.id}>{model.name} · {model.algorithm}</option>)}</select></label>
    </div>
    <div className="an-filter-actions"><span>{filters.time_range === "custom" && (!filters.from_date || !filters.to_date) ? "Choose both dates to load this range." : "Filters refresh analytics automatically."}</span><button type="button" className="an-button an-button--quiet" disabled={!changed} onClick={reset}><RotateCcw size={15}/> Reset Filters</button></div>
  </section>;
}
