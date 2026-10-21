
import { CheckSquare, Plus, X } from "lucide-react";

export default function DatasetSelectionBar({
  selectedCount = 0,
  totalMatching = 0,
  allMatching = false,
  loading = false,
  disabled = false,
  onSelectAllMatching,
  onClearSelection,
  onCreateDataset,
  canManage = true,
  className = "",
}) {
  const hasSelection = selectedCount > 0;
  const isDisabled = disabled || loading;

  return (
    <section
      className={`dataset-selection-bar ${
        hasSelection ? "dataset-selection-bar--active" : ""
      } ${className}`.trim()}
      aria-label="Dataset selection"
    >
      <div className="dataset-selection-bar__info">
        <div className="dataset-selection-bar__icon">
          <CheckSquare size={18} aria-hidden="true" />
        </div>

        <div className="dataset-selection-bar__text">
          <strong className="dataset-selection-bar__count">
            {selectedCount.toLocaleString()} selected
          </strong>

          <span className="dataset-selection-bar__description">
            {allMatching
              ? `All ${totalMatching.toLocaleString()} matching emails selected`
              : `${totalMatching.toLocaleString()} emails match the current filters`}
          </span>
        </div>
      </div>

      <div className="dataset-selection-bar__actions">
        <button
          type="button"
          className="dataset-button dataset-button--secondary"
          onClick={onSelectAllMatching}
          disabled={
            isDisabled ||
            totalMatching === 0 ||
            allMatching
          }
          title="Select every email matching the current filters"
        >
          <CheckSquare size={16} aria-hidden="true" />
          <span>
            {allMatching ? "All Matching Selected" : "Select All Matching"}
          </span>
        </button>

        {canManage && <button
          type="button"
          className="dataset-button dataset-button--ghost"
          onClick={onClearSelection}
          disabled={isDisabled || !hasSelection}
          title="Clear the current selection"
        >
          <X size={16} aria-hidden="true" />
          <span>Clear Selection</span>
        </button>}

        <button
          type="button"
          className="dataset-button dataset-button--primary"
          onClick={onCreateDataset}
          disabled={isDisabled || !hasSelection}
        >
          <Plus size={16} aria-hidden="true" />
          <span>Create Dataset</span>
        </button>
      </div>
    </section>
  );
}
