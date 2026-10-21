import {
  Download,
  FileJson,
  FileSpreadsheet,
  Info,
  LoaderCircle,
} from "lucide-react";

const FORMATS = [
  {
    value: "csv",
    label: "CSV",
    description: "Comma-separated values",
    icon: FileSpreadsheet,
  },
  {
    value: "json",
    label: "JSON",
    description: "JavaScript Object Notation",
    icon: FileJson,
  },
];

const SPLITS = [
  { value: "all", label: "Entire Dataset" },
  { value: "train", label: "Training Set" },
  { value: "validation", label: "Validation Set" },
  { value: "test", label: "Test Set" },
];

function getDatasetId(dataset) {
  return dataset?.dataset_id ?? dataset?.id ?? "";
}

function getVersionId(version) {
  return version?.version_id ?? version?.id ?? "";
}

export default function DatasetExportPanel({
  datasets = [],
  versions = [],
  datasetId = "",
  versionId = "",
  format = "csv",
  split = "all",
  loading = false,
  exporting = false,
  disabled = false,
  error = "",
  onDatasetChange,
  onVersionChange,
  onFormatChange,
  onSplitChange,
  onExport,
  className = "",
}) {
  const selectedDataset =
    datasets.find(
      (item) => String(getDatasetId(item)) === String(datasetId)
    ) ?? null;

  const selectedVersion =
    versions.find(
      (item) => String(getVersionId(item)) === String(versionId)
    ) ?? null;

  const canExport =
    Boolean(datasetId) &&
    Boolean(versionId) &&
    Boolean(format) &&
    Boolean(split) &&
    !loading &&
    !exporting &&
    !disabled;

  return (
    <section
      className={`dataset-export-panel ${className}`.trim()}
      aria-label="Dataset export configuration"
    >
      <div className="dataset-export-panel__header">
        <div>
          <h2>Export Configuration</h2>
          <p>Choose a dataset version, format, and split.</p>
        </div>
      </div>

      <div className="dataset-export-panel__fields">
        <div className="dataset-export-field">
          <label htmlFor="export-dataset">Dataset</label>

          <select
            id="export-dataset"
            value={datasetId}
            onChange={(event) =>
              onDatasetChange?.(event.target.value)
            }
            disabled={loading || disabled || exporting}
          >
            <option value="">Select a dataset</option>

            {datasets.map((dataset) => {
              const id = getDatasetId(dataset);

              return (
                <option key={id} value={id}>
                  {dataset.name ?? dataset.dataset_name ?? id}
                </option>
              );
            })}
          </select>
        </div>

        <div className="dataset-export-field">
          <label htmlFor="export-version">Dataset Version</label>

          <select
            id="export-version"
            value={versionId}
            onChange={(event) =>
              onVersionChange?.(event.target.value)
            }
            disabled={
              !datasetId ||
              loading ||
              disabled ||
              exporting ||
              versions.length === 0
            }
          >
            <option value="">Select a version</option>

            {versions.map((version) => {
              const id = getVersionId(version);

              return (
                <option key={id} value={id}>
                  {version.name ??
                    version.version_name ??
                    `Version ${id}`}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {selectedDataset && (
        <div className="dataset-export-panel__selection">
          <span>
            Dataset:{" "}
            <strong>
              {selectedDataset.name ??
                selectedDataset.dataset_name ??
                datasetId}
            </strong>
          </span>

          {selectedVersion && (
            <span>
              Version:{" "}
              <strong>
                {selectedVersion.name ??
                  selectedVersion.version_name ??
                  versionId}
              </strong>
            </span>
          )}
        </div>
      )}

      <div className="dataset-export-panel__section">
        <h3>Export Format</h3>

        <div
          className="dataset-export-panel__formats"
          role="group"
          aria-label="Export format"
        >
          {FORMATS.map((item) => {
            const Icon = item.icon;
            const selected = format === item.value;

            return (
              <button
                key={item.value}
                type="button"
                className={`dataset-export-format ${
                  selected ? "is-selected" : ""
                }`}
                aria-pressed={selected}
                onClick={() => onFormatChange?.(item.value)}
                disabled={disabled || exporting}
              >
                <Icon size={22} />

                <span className="dataset-export-format__content">
                  <strong>{item.label}</strong>
                  <small>{item.description}</small>
                </span>

                <span
                  className="dataset-export-format__radio"
                  aria-hidden="true"
                />
              </button>
            );
          })}
        </div>
      </div>

      <div className="dataset-export-panel__section">
        <h3>Dataset Split</h3>

        <div className="dataset-export-field">
          <label htmlFor="export-split">
            Select data to export
          </label>

          <select
            id="export-split"
            value={split}
            onChange={(event) =>
              onSplitChange?.(event.target.value)
            }
            disabled={
              !versionId || disabled || exporting
            }
          >
            {SPLITS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <p className="dataset-export-panel__hint">
          Export the complete version or an individual split.
        </p>
      </div>

      {error && (
        <div
          className="dataset-export-panel__error"
          role="alert"
        >
          <Info size={17} />
          <span>{error}</span>
        </div>
      )}

      <div className="dataset-export-panel__footer">
        <div className="dataset-export-panel__notice">
          <Info size={16} />

          <span>
            Exports use the canonical ground truth and F1–F12
            feature values stored in the selected dataset version.
          </span>
        </div>

        <button
          type="button"
          className="dataset-button dataset-button--primary"
          onClick={onExport}
          disabled={!canExport}
        >
          {exporting ? (
            <LoaderCircle
              size={17}
              className="dataset-icon--spinning"
            />
          ) : (
            <Download size={17} />
          )}

          {exporting ? "Exporting..." : "Export Dataset"}
        </button>
      </div>
    </section>
  );
}