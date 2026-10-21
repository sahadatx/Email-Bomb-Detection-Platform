import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Database,
  Loader2,
  RefreshCw,
} from "lucide-react";

import {
  getDatasetSelection,
  getPreprocessingErrorMessage,
} from "../services/preprocessingService";

import {
  getDatasets,
  getVersionsForDataset,
} from "../../datasets/services/datasetService";

// ============================================================================
// CONSTANTS
// ============================================================================

const DATASET_PAGE_SIZE = 100;

// ============================================================================
// RESPONSE HELPERS
// ============================================================================

function getArrayFromResponse(response, keys = []) {
  if (Array.isArray(response)) {
    return response;
  }

  if (!response || typeof response !== "object") {
    return [];
  }

  for (const key of keys) {
    if (Array.isArray(response[key])) {
      return response[key];
    }
  }

  if (response.data && typeof response.data === "object") {
    for (const key of keys) {
      if (Array.isArray(response.data[key])) {
        return response.data[key];
      }
    }

    if (Array.isArray(response.data.items)) {
      return response.data.items;
    }

    if (Array.isArray(response.data.results)) {
      return response.data.results;
    }
  }

  if (Array.isArray(response.items)) {
    return response.items;
  }

  if (Array.isArray(response.results)) {
    return response.results;
  }

  return [];
}

function getVersionData(selection) {
  return (
    selection?.dataset_version ??
    selection?.version ??
    selection ??
    null
  );
}

function getDatasetId(dataset) {
  return dataset?.id ?? dataset?.dataset_id ?? "";
}

function getDatasetName(dataset) {
  return (
    dataset?.name ??
    dataset?.dataset_name ??
    dataset?.title ??
    "Unnamed dataset"
  );
}

function getVersionId(version) {
  return version?.id ?? version?.version_id ?? "";
}

function getVersionLabel(version) {
  if (
    version?.version_number !== null &&
    version?.version_number !== undefined
  ) {
    return `v${version.version_number}`;
  }

  if (typeof version?.version === "string") {
    return version.version;
  }

  if (
    typeof version?.version === "number" &&
    Number.isFinite(version.version)
  ) {
    return `v${version.version}`;
  }

  if (typeof version?.name === "string" && version.name.trim()) {
    return version.name;
  }

  return "Unnamed version";
}

function getFeatureCount(version) {
  const schema = version?.feature_schema;

  if (Array.isArray(schema)) {
    return schema.length;
  }

  if (schema && typeof schema === "object") {
    if (Number.isFinite(Number(schema.feature_count))) {
      return Number(schema.feature_count);
    }

    if (Array.isArray(schema.features)) {
      return schema.features.length;
    }

    // Some API responses expose a flat { F1: type, ... } schema.
    return Object.keys(schema).filter((key) =>
      /^F(?:[1-9]|1[0-2])$/.test(key)
    ).length;
  }

  return version?.feature_count ?? null;
}

function isValidated(version) {
  return (
    version?.validation_passed === true ||
    version?.is_validated === true ||
    version?.status === "validated"
  );
}

function getValidationLabel(version) {
  if (version?.validation_passed === true) {
    return "Passed";
  }

  if (version?.validation_passed === false) {
    return "Not passed";
  }

  if (version?.is_validated === true) {
    return "Passed";
  }

  return version?.status ?? "Not available";
}

function getSampleCount(version) {
  const count =
    version?.sample_count ??
    version?.total_samples ??
    version?.samples_count;

  if (count === null || count === undefined) {
    return "—";
  }

  const numericCount = Number(count);

  return Number.isFinite(numericCount)
    ? numericCount.toLocaleString()
    : "—";
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function DatasetSelector({
  value = "",
  onSelectionChange,
  disabled = false,
}) {
  const [datasets, setDatasets] = useState([]);
  const [versions, setVersions] = useState([]);

  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [selectedVersionId, setSelectedVersionId] = useState(
    String(value ?? ""),
  );

  const [selection, setSelection] = useState(null);

  const [datasetsLoading, setDatasetsLoading] = useState(false);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [selectionLoading, setSelectionLoading] = useState(false);

  const [error, setError] = useState("");
  const [datasetError, setDatasetError] = useState("");
  const [versionError, setVersionError] = useState("");

  const version = selection ? getVersionData(selection) : null;
  const featureCount = version ? getFeatureCount(version) : null;

  const selectedDataset = useMemo(
    () =>
      datasets.find(
        (dataset) => String(getDatasetId(dataset)) === selectedDatasetId,
      ) ?? null,
    [datasets, selectedDatasetId],
  );

  // ==========================================================================
  // LOAD DATASETS
  // ==========================================================================

  const loadDatasets = useCallback(async () => {
    setDatasetsLoading(true);
    setDatasetError("");

    try {
      const response = await getDatasets({
        page: 1,
        page_size: DATASET_PAGE_SIZE,
      });

      const items = getArrayFromResponse(response, [
        "datasets",
        "items",
        "results",
      ]);

      setDatasets(items);
    } catch (requestError) {
      setDatasets([]);
      setDatasetError(getPreprocessingErrorMessage(requestError));
    } finally {
      setDatasetsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  // ==========================================================================
  // LOAD VERSIONS WHEN DATASET CHANGES
  // ==========================================================================

  const loadVersions = useCallback(async (datasetId) => {
    if (!datasetId) {
      setVersions([]);
      setSelectedVersionId("");
      setSelection(null);
      return;
    }

    setVersionsLoading(true);
    setVersionError("");
    setVersions([]);
    setSelectedVersionId("");
    setSelection(null);
    setError("");
    onSelectionChange?.(null);

    try {
      const response = await getVersionsForDataset(datasetId, {
        page: 1,
        page_size: DATASET_PAGE_SIZE,
      });

      const items = getArrayFromResponse(response, [
        "versions",
        "items",
        "results",
      ]);

      setVersions(items);
    } catch (requestError) {
      setVersions([]);
      setVersionError(getPreprocessingErrorMessage(requestError));
    } finally {
      setVersionsLoading(false);
    }
  }, [onSelectionChange]);

  // ==========================================================================
  // RESTORE CURRENT VERSION VALUE
  // ==========================================================================

  useEffect(() => {
    const nextValue = String(value ?? "");

    if (!nextValue) {
      setSelectedVersionId("");
      setSelection(null);
      return;
    }

    setSelectedVersionId((current) =>
      current === nextValue ? current : nextValue,
    );
  }, [value]);

  // ==========================================================================
  // DATASET CHANGE
  // ==========================================================================

  function handleDatasetChange(event) {
    const datasetId = event.target.value;

    setSelectedDatasetId(datasetId);
    setSelectedVersionId("");
    setVersions([]);
    setSelection(null);
    setError("");
    setVersionError("");
    onSelectionChange?.(null);

    if (datasetId) {
      loadVersions(datasetId);
    }
  }

  // ==========================================================================
  // VERSION CHANGE
  // ==========================================================================

  function handleVersionChange(event) {
    const versionId = event.target.value;

    setSelectedVersionId(versionId);
    setSelection(null);
    setError("");
    onSelectionChange?.(null);
  }

  // ==========================================================================
  // LOAD SELECTED VERSION
  // ==========================================================================

  async function handleLoadDataset(event) {
    event.preventDefault();

    if (!selectedDatasetId) {
      setError("Select a dataset first.");
      return;
    }

    if (!selectedVersionId) {
      setError("Select a dataset version.");
      return;
    }

    const selectedVersion = versions.find(
      (item) => String(getVersionId(item)) === selectedVersionId,
    );

    if (!selectedVersion) {
      setError("The selected dataset version is unavailable.");
      return;
    }

    if (!isValidated(selectedVersion)) {
      setError("Only validated dataset versions can be loaded.");
      return;
    }

    setSelectionLoading(true);
    setError("");
    setSelection(null);
    onSelectionChange?.(null);

    try {
      const result = await getDatasetSelection(selectedVersionId);
      const loadedVersion = getVersionData(result);

      if (!loadedVersion || typeof loadedVersion !== "object") {
        throw new Error("The API returned an invalid dataset version.");
      }

      if (!isValidated(loadedVersion)) {
        throw new Error(
          "The selected dataset version is not validated.",
        );
      }

      // Preserve the selected dataset metadata for the split panel.
      // The backend selection response intentionally contains only
      // dataset_id, while the selector already has the dataset name.
      const enrichedResult = {
        ...result,
        dataset_version_id:
          result.dataset_version_id ?? selectedVersionId,
        dataset: selectedDataset,
      };

      setSelection(enrichedResult);
      onSelectionChange?.(enrichedResult);
    } catch (requestError) {
      setSelection(null);
      onSelectionChange?.(null);
      setError(getPreprocessingErrorMessage(requestError));
    } finally {
      setSelectionLoading(false);
    }
  }

  // ==========================================================================
  // RESET
  // ==========================================================================

  function handleReset() {
    setSelectedDatasetId("");
    setSelectedVersionId("");
    setVersions([]);
    setSelection(null);
    setError("");
    setDatasetError("");
    setVersionError("");
    onSelectionChange?.(null);
  }

  // ==========================================================================
  // REFRESH
  // ==========================================================================

  async function handleRefresh() {
    setError("");
    setVersionError("");
    setSelection(null);
    onSelectionChange?.(null);

    await loadDatasets();

    if (selectedDatasetId) {
      await loadVersions(selectedDatasetId);
    }
  }

  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <section
      className="preprocessing-panel preprocessing-dataset-selector"
      aria-labelledby="dataset-selector-title"
    >
      <div className="preprocessing-panel-heading">
        <div className="preprocessing-heading-icon">
          <Database size={20} aria-hidden="true" />
        </div>

        <div className="preprocessing-heading-copy">
          <h2 id="dataset-selector-title">Dataset Selection</h2>
          <p>
            Select a dataset and a validated version from Dataset
            Management.
          </p>
        </div>

        <span className="preprocessing-readonly-badge">
          Validated only
        </span>
      </div>

      <form onSubmit={handleLoadDataset}>
        <div className="preprocessing-form-field">
          <label htmlFor="preprocessing-dataset">
            Dataset
          </label>

          <select
            id="preprocessing-dataset"
            name="dataset_id"
            value={selectedDatasetId}
            onChange={handleDatasetChange}
            disabled={disabled || datasetsLoading}
            aria-invalid={Boolean(datasetError)}
            aria-describedby={
              datasetError
                ? "preprocessing-dataset-list-error"
                : "preprocessing-dataset-help"
            }
          >
            <option value="">
              {datasetsLoading
                ? "Loading datasets..."
                : "Select a dataset"}
            </option>

            {datasets.map((dataset) => {
              const id = getDatasetId(dataset);

              if (!id) {
                return null;
              }

              return (
                <option key={id} value={String(id)}>
                  {getDatasetName(dataset)}
                </option>
              );
            })}
          </select>

          <small id="preprocessing-dataset-help">
            Choose an existing dataset. Creation and editing are
            managed in Module 05.
          </small>
        </div>

        {datasetError && (
          <div
            id="preprocessing-dataset-list-error"
            className="preprocessing-inline-error"
            role="alert"
          >
            <AlertCircle size={17} aria-hidden="true" />
            <span>{datasetError}</span>
          </div>
        )}

        {!datasetsLoading &&
          !datasetError &&
          datasets.length === 0 && (
            <div className="preprocessing-inline-error" role="status">
              <AlertCircle size={17} aria-hidden="true" />
              <span>No datasets are available.</span>
            </div>
          )}

        <div className="preprocessing-form-field">
          <label htmlFor="preprocessing-dataset-version">
            Dataset Version
          </label>

          <select
            id="preprocessing-dataset-version"
            name="dataset_version_id"
            value={selectedVersionId}
            onChange={handleVersionChange}
            disabled={
              disabled ||
              !selectedDatasetId ||
              versionsLoading ||
              selectionLoading
            }
            aria-invalid={Boolean(versionError)}
            aria-describedby={
              versionError
                ? "preprocessing-version-list-error"
                : "preprocessing-version-help"
            }
          >
            <option value="">
              {!selectedDatasetId
                ? "Select a dataset first"
                : versionsLoading
                  ? "Loading versions..."
                  : "Select a validated version"}
            </option>

            {versions
              .filter(isValidated)
              .map((item) => {
                const id = getVersionId(item);

                if (!id) {
                  return null;
                }

                return (
                  <option key={id} value={String(id)}>
                    {getVersionLabel(item)}
                  </option>
                );
              })}
          </select>

          <small id="preprocessing-version-help">
            Only versions marked as validated are available for
            preprocessing.
          </small>
        </div>

        {versionError && (
          <div
            id="preprocessing-version-list-error"
            className="preprocessing-inline-error"
            role="alert"
          >
            <AlertCircle size={17} aria-hidden="true" />
            <span>{versionError}</span>
          </div>
        )}

        {selectedDatasetId &&
          !versionsLoading &&
          !versionError &&
          versions.filter(isValidated).length === 0 && (
            <div className="preprocessing-inline-error" role="status">
              <AlertCircle size={17} aria-hidden="true" />
              <span>
                This dataset has no validated versions available.
              </span>
            </div>
          )}

        <div className="preprocessing-form-actions">
          <button
            type="submit"
            className="preprocessing-primary-button"
            disabled={
              disabled ||
              datasetsLoading ||
              versionsLoading ||
              selectionLoading ||
              !selectedDatasetId ||
              !selectedVersionId
            }
          >
            {selectionLoading ? (
              <>
                <Loader2
                  size={16}
                  className="preprocessing-spinner"
                  aria-hidden="true"
                />
                Loading dataset...
              </>
            ) : (
              <>
                <Database size={16} aria-hidden="true" />
                Load Dataset
              </>
            )}
          </button>

          <button
            type="button"
            className="preprocessing-secondary-button"
            onClick={handleReset}
            disabled={disabled || selectionLoading}
          >
            <RefreshCw size={15} aria-hidden="true" />
            Reset
          </button>

          <button
            type="button"
            className="preprocessing-secondary-button"
            onClick={handleRefresh}
            disabled={disabled || datasetsLoading || versionsLoading}
          >
            <RefreshCw size={15} aria-hidden="true" />
            Refresh
          </button>
        </div>
      </form>

      {error && (
        <div
          className="preprocessing-inline-error"
          role="alert"
        >
          <AlertCircle size={17} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {selection && version && (
        <div
          className="preprocessing-dataset-result"
          aria-live="polite"
        >
          <div className="preprocessing-dataset-result-heading">
            <div>
              <span className="preprocessing-result-eyebrow">
                Selected dataset version
              </span>

              <h3>
                {getDatasetName(selectedDataset ?? version)}
              </h3>

              <p className="preprocessing-dataset-id">
                Version ID: {getVersionId(version) || selectedVersionId}
              </p>
            </div>

            <span className="preprocessing-validated-status">
              <CheckCircle2 size={15} aria-hidden="true" />
              Validated
            </span>
          </div>

          <div className="preprocessing-dataset-metadata">
            <div>
              <span>Version</span>
              <strong>{getVersionLabel(version)}</strong>
            </div>

            <div>
              <span>Validation</span>
              <strong>{getValidationLabel(version)}</strong>
            </div>

            <div>
              <span>Features</span>
              <strong>{featureCount ?? "—"}</strong>
            </div>

            <div>
              <span>Samples</span>
              <strong>{getSampleCount(version)}</strong>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
