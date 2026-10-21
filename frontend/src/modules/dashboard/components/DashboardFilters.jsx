import { RotateCcw, SlidersHorizontal } from "lucide-react";
import {
  CLASSIFICATIONS,
  RISK_LEVELS,
  TIME_RANGES,
} from "../utils/dashboardConstants";

function SelectFilter({ label, name, value, options, onChange }) {
  return (
    <label className="dashboard-filter">
      <span>{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(name, event.target.value)}
      >
        {options.map(([optionValue, text]) => (
          <option key={optionValue || "all"} value={optionValue}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function DashboardFilters({
  filters,
  modelOptions = [],
  onChange,
  onReset,
}) {
  const models = [
    ["", "All models"],
    ...modelOptions.map((model) => [
      model.id,
      `${model.name} · ${model.algorithm}`,
    ]),
  ];
  return (
    <section className="dashboard-filter-panel" aria-label="Dashboard filters">
      <div className="dashboard-filter-heading">
        <div>
          <SlidersHorizontal size={16} />
          <strong>Filters</strong>
          <span>Changes refresh dashboard data automatically</span>
        </div>
      </div>
      <div className="dashboard-filter-grid">
        <SelectFilter
          label="Time range"
          name="time_range"
          value={filters.time_range}
          options={TIME_RANGES}
          onChange={onChange}
        />
        <SelectFilter
          label="Classification"
          name="classification"
          value={filters.classification}
          options={CLASSIFICATIONS}
          onChange={onChange}
        />
        <SelectFilter
          label="Risk level"
          name="risk_level"
          value={filters.risk_level}
          options={RISK_LEVELS}
          onChange={onChange}
        />
        <SelectFilter
          label="Model"
          name="model_id"
          value={filters.model_id}
          options={models}
          onChange={onChange}
        />
        {filters.time_range === "custom" && (
          <>
            <label className="dashboard-filter">
              <span>From</span>
              <input
                type="datetime-local"
                value={filters.start_date}
                onChange={(event) => onChange("start_date", event.target.value)}
              />
            </label>
            <label className="dashboard-filter">
              <span>To</span>
              <input
                type="datetime-local"
                value={filters.end_date}
                onChange={(event) => onChange("end_date", event.target.value)}
              />
            </label>
          </>
        )}
      </div>
      <div className="dashboard-filter-actions">
        <button type="button" className="dashboard-reset" onClick={onReset}>
          <RotateCcw size={14} /> Reset Filters
        </button>
      </div>
      {filters.time_range === "custom" &&
        (!filters.start_date || !filters.end_date) && (
          <p className="dashboard-filter-hint">
            Choose both dates to load the selected range.
          </p>
        )}
    </section>
  );
}
