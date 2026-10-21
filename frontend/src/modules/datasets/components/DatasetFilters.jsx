
import React from "react";
import { RotateCcw, Search } from "lucide-react";
import {
  DATASET_LABELS,
  DATASET_SOURCES,
  createDefaultDatasetFilters,
} from "../types";

/**
 * Dataset Management — Workspace Filters
 *
 * Search fields:
 * - Subject
 * - Sender
 * - Message-ID
 * - Source Identifier
 *
 * All filters are controlled by the parent page.
 */

export default function DatasetFilters({
  filters = createDefaultDatasetFilters(),
  onChange,
  onReset,
  disabled = false,
  className = "",
}) {
  const updateFilter = (name, value) => {
    onChange?.({
      ...filters,
      [name]: value,
    });
  };

  const handleReset = () => {
    onReset?.();
    if (!onReset) {
      onChange?.(createDefaultDatasetFilters());
    }
  };

  return (
    <section
      className={`dataset-filters ${className}`.trim()}
      aria-label="Filter dataset emails"
    >
      <div className="dataset-filters__fields">
        <div className="dataset-filter dataset-filter--search">
          <label htmlFor="dataset-search" className="dataset-filter__label">
            Search
          </label>

          <div className="dataset-filter__search-control">
            <Search
              className="dataset-filter__search-icon"
              size={17}
              aria-hidden="true"
            />
            <input
              id="dataset-search"
              type="search"
              className="dataset-filter__input"
              placeholder="Subject, sender, Message-ID, source identifier"
              value={filters.search ?? ""}
              onChange={(event) =>
                updateFilter("search", event.target.value)
              }
              disabled={disabled}
              autoComplete="off"
            />
          </div>
        </div>

        <div className="dataset-filter">
          <label
            htmlFor="dataset-ground-truth"
            className="dataset-filter__label"
          >
            Ground Truth
          </label>

          <select
            id="dataset-ground-truth"
            className="dataset-filter__input"
            value={filters.ground_truth ?? ""}
            onChange={(event) =>
              updateFilter("ground_truth", event.target.value)
            }
            disabled={disabled}
          >
            <option value="">All Ground Truth</option>
            <option value={DATASET_LABELS.NORMAL}>Normal</option>
            <option value={DATASET_LABELS.BOMBING}>Bombing</option>
          </select>
        </div>

        <div className="dataset-filter">
          <label htmlFor="dataset-source" className="dataset-filter__label">
            Source
          </label>

          <select
            id="dataset-source"
            className="dataset-filter__input"
            value={filters.source ?? ""}
            onChange={(event) =>
              updateFilter("source", event.target.value)
            }
            disabled={disabled}
          >
            <option value="">All Sources</option>
            <option value={DATASET_SOURCES.FILE_UPLOAD}>
              File Upload
            </option>
            <option value={DATASET_SOURCES.RAW_EMAIL}>
              Raw Email
            </option>
          </select>
        </div>

        <div className="dataset-filter">
          <label htmlFor="dataset-from-date" className="dataset-filter__label">
            From
          </label>

          <input
            id="dataset-from-date"
            type="date"
            className="dataset-filter__input"
            value={filters.from_date ?? ""}
            onChange={(event) =>
              updateFilter("from_date", event.target.value)
            }
            disabled={disabled}
          />
        </div>

        <div className="dataset-filter">
          <label htmlFor="dataset-to-date" className="dataset-filter__label">
            To
          </label>

          <input
            id="dataset-to-date"
            type="date"
            className="dataset-filter__input"
            value={filters.to_date ?? ""}
            min={filters.from_date || undefined}
            onChange={(event) =>
              updateFilter("to_date", event.target.value)
            }
            disabled={disabled}
          />
        </div>
      </div>

      <div className="dataset-filters__actions">
        <button
          type="button"
          className="dataset-button dataset-button--secondary"
          onClick={handleReset}
          disabled={disabled}
        >
          <RotateCcw size={16} aria-hidden="true" />
          <span>Reset Filters</span>
        </button>
      </div>
    </section>
  );
}