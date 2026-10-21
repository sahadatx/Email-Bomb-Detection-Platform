import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useAuth } from "../../../core/auth/AuthProvider";
import { useSearchParams } from "react-router-dom";
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  RefreshCw,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";

import * as datasetService from "../services/datasetService";
import DatasetValidationSummary from "../components/DatasetValidationSummary";
import DatasetValidationIssues from "../components/DatasetValidationIssues";

// ============================================================================
// RESPONSE HELPERS
// ============================================================================

function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const location = Array.isArray(item?.loc)
          ? item.loc.join(".")
          : "";

        const message =
          item?.msg ??
          item?.message ??
          String(item);

        return location
          ? `${location}: ${message}`
          : message;
      })
      .join("; ");
  }

  return (
    error?.response?.data?.message ??
    error?.message ??
    fallback
  );
}

function getItems(response) {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response?.items)) {
    return response.items;
  }

  if (Array.isArray(response?.data)) {
    return response.data;
  }

  if (Array.isArray(response?.data?.items)) {
    return response.data.items;
  }

  if (Array.isArray(response?.results)) {
    return response.results;
  }

  return [];
}

function getDatasetId(dataset) {
  return String(
    dataset?.id ??
    dataset?.dataset_id ??
    ""
  );
}

function getVersionId(version) {
  return String(
    version?.id ??
    version?.version_id ??
    ""
  );
}

function getDatasetName(dataset) {
  return (
    dataset?.name ??
    dataset?.title ??
    "Unnamed dataset"
  );
}

function getVersionLabel(version) {
  const name = version?.name;
  const number =
    version?.version_number ??
    version?.version;

  if (name && number !== undefined && number !== null) {
    return `${name} (v${number})`;
  }

  if (name) {
    return name;
  }

  if (number !== undefined && number !== null) {
    return `Version ${number}`;
  }

  return getVersionId(version) || "Unnamed version";
}

function getValidationResult(response) {
  if (!response || typeof response !== "object") {
    return null;
  }

  // Support APIs that wrap the result in a data property.
  if (
    response.data &&
    typeof response.data === "object" &&
    !Array.isArray(response.data)
  ) {
    return response.data;
  }

  return response;
}

function getIssues(validation) {
  if (Array.isArray(validation?.issues)) {
    return validation.issues;
  }

  if (Array.isArray(validation?.data?.issues)) {
    return validation.data.issues;
  }

  return [];
}

function getChecks(validation) {
  if (Array.isArray(validation?.checks)) {
    return validation.checks;
  }

  if (Array.isArray(validation?.data?.checks)) {
    return validation.data.checks;
  }

  return [];
}

function getSummary(validation) {
  return (
    validation?.summary ??
    validation?.run?.summary ??
    validation?.data?.summary ??
    validation?.data?.run?.summary ??
    null
  );
}

function formatCount(value) {
  if (
    value === undefined ||
    value === null ||
    value === ""
  ) {
    return "—";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return String(value);
  }

  return number.toLocaleString();
}

function getSampleCount(version, dataset, field) {
  const value =
    version?.[field] ??
    dataset?.[field];

  return formatCount(value);
}

function getCheckStatus(check) {
  if (check?.passed === true) {
    return "passed";
  }

  const severity = String(
    check?.severity ?? check?.status ?? ""
  ).toLowerCase();

  if (
    severity === "warning" ||
    severity === "warn"
  ) {
    return "warning";
  }

  return "failed";
}

function getCheckLabel(status) {
  if (status === "passed") {
    return "Passed";
  }

  if (status === "warning") {
    return "Warning";
  }

  return "Failed";
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function DatasetValidation() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);
  const [searchParams] = useSearchParams();

  const initialVersionId =
    searchParams.get("version_id") ?? "";

  // --------------------------------------------------------------------------
  // STATE
  // --------------------------------------------------------------------------

  const [datasets, setDatasets] = useState([]);
  const [versions, setVersions] = useState([]);

  const [selectedDatasetId, setSelectedDatasetId] =
    useState("");

  const [selectedVersionId, setSelectedVersionId] =
    useState(initialVersionId);

  const [validation, setValidation] = useState(null);

  const [datasetsLoading, setDatasetsLoading] =
    useState(true);

  const [versionsLoading, setVersionsLoading] =
    useState(false);

  const [validating, setValidating] =
    useState(false);

  const [error, setError] = useState("");
  const [versionsError, setVersionsError] =
    useState("");

  // --------------------------------------------------------------------------
  // DERIVED DATA
  // --------------------------------------------------------------------------

  const selectedDataset = useMemo(
    () =>
      datasets.find(
        (dataset) =>
          getDatasetId(dataset) === selectedDatasetId
      ) ?? null,
    [datasets, selectedDatasetId]
  );

  const selectedVersion = useMemo(
    () =>
      versions.find(
        (version) =>
          getVersionId(version) === selectedVersionId
      ) ?? null,
    [versions, selectedVersionId]
  );

  const currentIssues = useMemo(
    () => getIssues(validation),
    [validation]
  );

  const currentChecks = useMemo(
    () => getChecks(validation),
    [validation]
  );

  const currentSummary = useMemo(
    () => getSummary(validation),
    [validation]
  );

  const canValidate =
    Boolean(selectedVersionId) &&
    !datasetsLoading &&
    !versionsLoading &&
    !validating;

  // --------------------------------------------------------------------------
  // LOAD DATASETS
  // --------------------------------------------------------------------------

  const loadDatasets = useCallback(async () => {
    setDatasetsLoading(true);
    setError("");

    try {
      const response =
        await datasetService.getDatasets({
          page: 1,
          page_size: 100,
        });

      const items = getItems(response);

      setDatasets(items);

      return items;
    } catch (err) {
      setDatasets([]);

      setError(
        getErrorMessage(
          err,
          "Unable to load datasets."
        )
      );

      return [];
    } finally {
      setDatasetsLoading(false);
    }
  }, []);

  // --------------------------------------------------------------------------
  // LOAD DATASET VERSIONS
  // --------------------------------------------------------------------------

  const loadVersions = useCallback(
    async (datasetId, preferredVersionId = "") => {
      if (!datasetId) {
        setVersions([]);
        setSelectedVersionId("");
        setVersionsError("");
        return [];
      }

      setVersionsLoading(true);
      setVersionsError("");

      try {
        const response =
          await datasetService.getDatasetVersions({
            dataset_id: datasetId,
            page: 1,
            page_size: 100,
          });

        const items = getItems(response);

        setVersions(items);

        setSelectedVersionId((currentId) => {
          const requestedId =
            preferredVersionId || currentId;

          if (
            requestedId &&
            items.some(
              (item) =>
                getVersionId(item) === requestedId
            )
          ) {
            return requestedId;
          }

          return "";
        });

        return items;
      } catch (err) {
        setVersions([]);
        setSelectedVersionId("");

        setVersionsError(
          getErrorMessage(
            err,
            "Unable to load dataset versions."
          )
        );

        return [];
      } finally {
        setVersionsLoading(false);
      }
    },
    []
  );

  // --------------------------------------------------------------------------
  // INITIAL LOAD AND URL VERSION RESOLUTION
  // --------------------------------------------------------------------------

  useEffect(() => {
    let active = true;

    async function initialize() {
      const datasetItems = await loadDatasets();

      if (!active || !initialVersionId) {
        return;
      }

      try {
        // Resolve the selected version so its dataset can be selected.
        const version =
          await datasetService.getDatasetVersion(
            initialVersionId
          );

        if (!active) {
          return;
        }

        const versionData =
          version?.data &&
          typeof version.data === "object"
            ? version.data
            : version;

        const datasetId = String(
          versionData?.dataset_id ??
          versionData?.dataset?.id ??
          ""
        );

        if (!datasetId) {
          setError(
            "The selected version does not contain a dataset ID."
          );
          return;
        }

        const matchingDataset = datasetItems.find(
          (dataset) =>
            getDatasetId(dataset) === datasetId
        );

        if (!matchingDataset) {
          setError(
            "The dataset associated with this version could not be found."
          );
          return;
        }

        setSelectedDatasetId(datasetId);

        await loadVersions(
          datasetId,
          initialVersionId
        );
      } catch (err) {
        if (!active) {
          return;
        }

        setError(
          getErrorMessage(
            err,
            "Unable to resolve the selected dataset version."
          )
        );
      }
    }

    initialize();

    return () => {
      active = false;
    };
  }, [
    initialVersionId,
    loadDatasets,
    loadVersions,
  ]);

  // --------------------------------------------------------------------------
  // DATASET SELECTION
  // --------------------------------------------------------------------------

  const handleDatasetChange = useCallback(
    async (event) => {
      const datasetId = event.target.value;

      setSelectedDatasetId(datasetId);
      setSelectedVersionId("");
      setVersions([]);
      setValidation(null);
      setError("");
      setVersionsError("");

      if (datasetId) {
        await loadVersions(datasetId);
      }
    },
    [loadVersions]
  );

  // --------------------------------------------------------------------------
  // VERSION SELECTION
  // --------------------------------------------------------------------------

  const handleVersionChange = useCallback(
    (event) => {
      setSelectedVersionId(event.target.value);
      setValidation(null);
      setError("");
    },
    []
  );

  // --------------------------------------------------------------------------
  // RUN VALIDATION
  // --------------------------------------------------------------------------

  const handleValidate = useCallback(async () => {
    if (!selectedDatasetId) {
      setError("Select a dataset before running validation.");
      return;
    }

    if (!selectedVersionId) {
      setError(
        "Select a dataset version before running validation."
      );
      return;
    }

    setValidating(true);
    setError("");
    setValidation(null);

    try {
      const response =
        await datasetService.validateDatasetVersion(
          selectedVersionId
        );

      setValidation(getValidationResult(response));
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Dataset validation failed."
        )
      );
    } finally {
      setValidating(false);
    }
  }, [
    selectedDatasetId,
    selectedVersionId,
  ]);

  // --------------------------------------------------------------------------
  // REFRESH
  // --------------------------------------------------------------------------

  const handleRefresh = useCallback(async () => {
    setValidation(null);
    setError("");
    setVersionsError("");

    const datasetItems = await loadDatasets();

    if (!selectedDatasetId) {
      return;
    }

    const datasetStillExists = datasetItems.some(
      (dataset) =>
        getDatasetId(dataset) === selectedDatasetId
    );

    if (!datasetStillExists) {
      setSelectedDatasetId("");
      setSelectedVersionId("");
      setVersions([]);
      return;
    }

    await loadVersions(
      selectedDatasetId,
      selectedVersionId
    );
  }, [
    loadDatasets,
    loadVersions,
    selectedDatasetId,
    selectedVersionId,
  ]);

  // --------------------------------------------------------------------------
  // RENDER
  // --------------------------------------------------------------------------

  return (
    <main className="dataset-validation-page">
      {/* ================================================================== */}
      {/* PAGE HEADER                                                        */}
      {/* ================================================================== */}

      <header className="dataset-page-header">
        <div className="dataset-page-header__title">
          <div className="dataset-page-header__icon">
            <ClipboardCheck size={22} />
          </div>

          <div>
            <h1>Dataset Validation</h1>

            <p>
              Validate dataset quality, feature consistency,
              and class distribution before model training.
            </p>
          </div>
        </div>

        <div className="dataset-validation-page__header-actions">
          <button
            type="button"
            className="dataset-button dataset-button--secondary"
            onClick={handleRefresh}
            disabled={
              datasetsLoading ||
              versionsLoading ||
              validating
            }
          >
            <RefreshCw
              size={16}
              className={
                datasetsLoading || versionsLoading
                  ? "dataset-icon--spinning"
                  : ""
              }
            />

            Refresh
          </button>
        </div>
      </header>

      {/* ================================================================== */}
      {/* GLOBAL ERROR                                                        */}
      {/* ================================================================== */}

      {error && (
        <div
          className="dataset-alert dataset-alert--error"
          role="alert"
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* ================================================================== */}
      {/* DATASET AND VERSION SELECTION                                      */}
      {/* ================================================================== */}

      <section className="dataset-validation-page__selection">
        <div className="dataset-validation-page__section-heading">
          <div>
            <h2>Select Dataset Version</h2>

            <p>
              Choose the dataset and version you want to validate.
            </p>
          </div>
        </div>

        <div className="dataset-validation-page__selectors">
          {/* Dataset selector */}

          <div className="dataset-form-field">
            <label htmlFor="validation-dataset">
              Dataset
            </label>

            <select
              id="validation-dataset"
              value={selectedDatasetId}
              onChange={handleDatasetChange}
              disabled={
                datasetsLoading ||
                datasets.length === 0 ||
                validating
              }
            >
              <option value="">
                {datasetsLoading
                  ? "Loading datasets..."
                  : datasets.length === 0
                    ? "No datasets available"
                    : "Select dataset"}
              </option>

              {datasets.map((dataset) => {
                const datasetId =
                  getDatasetId(dataset);

                return (
                  <option
                    key={datasetId}
                    value={datasetId}
                  >
                    {getDatasetName(dataset)}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Version selector */}

          <div className="dataset-form-field">
            <label htmlFor="validation-version">
              Dataset Version
            </label>

            <select
              id="validation-version"
              value={selectedVersionId}
              onChange={handleVersionChange}
              disabled={
                !selectedDatasetId ||
                versionsLoading ||
                versions.length === 0 ||
                validating
              }
            >
              <option value="">
                {versionsLoading
                  ? "Loading versions..."
                  : !selectedDatasetId
                    ? "Select a dataset first"
                    : versions.length === 0
                      ? "No versions available"
                      : "Select version"}
              </option>

              {versions.map((version) => {
                const versionId =
                  getVersionId(version);

                return (
                  <option
                    key={versionId}
                    value={versionId}
                  >
                    {getVersionLabel(version)}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Validate action */}

          {canManage && <div className="dataset-validation-page__validate-action">
            <button
              type="button"
              className="dataset-button dataset-button--primary"
              onClick={handleValidate}
              disabled={!canValidate}
            >
              <ShieldCheck size={17} />

              {validating
                ? "Validating..."
                : "Validate Dataset"}
            </button>
          </div>}
        </div>

        {/* Version loading error */}

        {versionsError && (
          <div
            className="dataset-alert dataset-alert--error"
            role="alert"
          >
            <AlertCircle size={18} />
            <span>{versionsError}</span>
          </div>
        )}

        {/* Selected dataset information */}

        {selectedDataset && (
          <div className="dataset-validation-page__dataset-info">
            <div>
              <span>Selected Dataset</span>
              <strong>
                {getDatasetName(selectedDataset)}
              </strong>
            </div>

            <div>
              <span>Total Samples</span>
              <strong>
                {getSampleCount(
                  selectedVersion,
                  selectedDataset,
                  "sample_count"
                )}
              </strong>
            </div>

            <div>
              <span>Normal Samples</span>
              <strong>
                {getSampleCount(
                  selectedVersion,
                  selectedDataset,
                  "normal_count"
                )}
              </strong>
            </div>

            <div>
              <span>Bombing Samples</span>
              <strong>
                {getSampleCount(
                  selectedVersion,
                  selectedDataset,
                  "bombing_count"
                )}
              </strong>
            </div>
          </div>
        )}
      </section>

      {/* ================================================================== */}
      {/* VALIDATION SUMMARY                                                 */}
      {/* ================================================================== */}

      <DatasetValidationSummary
        validation={validation}
        loading={validating}
      />

      {/* ================================================================== */}
      {/* VALIDATION CHECKS                                                  */}
      {/* ================================================================== */}

      <section className="dataset-validation-page__checks">
        <div className="dataset-validation-page__section-heading">
          <div>
            <h2>Validation Checks</h2>

            <p>
              Checks returned by the backend for the selected version.
            </p>
          </div>

          <span className="dataset-validation-page__check-count">
            {validating
              ? "Loading..."
              : `${currentChecks.length} checks`}
          </span>
        </div>

        {/* Not run */}

        {!validation && !validating && (
          <div className="dataset-validation-page__empty">
            <ClipboardCheck size={24} />

            <strong>Validation not run</strong>

            <p>
              Select a dataset version and run validation
              to see its checks.
            </p>
          </div>
        )}

        {/* Running */}

        {validating && (
          <div
            className="dataset-validation-page__empty"
            role="status"
          >
            <span className="dataset-loading-spinner" />

            <p>Running dataset validation...</p>
          </div>
        )}

        {/* No checks returned */}

        {validation &&
          !validating &&
          currentChecks.length === 0 && (
            <div className="dataset-validation-page__empty">
              <AlertCircle size={24} />

              <strong>No checks returned</strong>

              <p>
                The validation response did not include
                individual checks.
              </p>
            </div>
          )}

        {/* Actual backend checks */}

        {validation &&
          !validating &&
          currentChecks.length > 0 && (
            <div className="dataset-validation-checks">
              {currentChecks.map((check, index) => {
                const status = getCheckStatus(check);

                const checkName =
                  check?.name ??
                  check?.code ??
                  "Validation Check";

                const checkKey =
                  check?.code ??
                  check?.name ??
                  `validation-check-${index}`;

                return (
                  <article
                    className={[
                      "dataset-validation-check",
                      `is-${status}`,
                    ].join(" ")}
                    key={checkKey}
                  >
                    <div className="dataset-validation-check__icon">
                      {status === "passed" ? (
                        <CheckCircle2 size={18} />
                      ) : status === "warning" ? (
                        <TriangleAlert size={18} />
                      ) : (
                        <AlertCircle size={18} />
                      )}
                    </div>

                    <div className="dataset-validation-check__content">
                      <div className="dataset-validation-check__title">
                        <strong>{checkName}</strong>

                        <span>
                          {getCheckLabel(status)}
                        </span>
                      </div>

                      {check?.message && (
                        <p>{check.message}</p>
                      )}

                      {Number(check?.affected_samples) > 0 && (
                        <small>
                          Affected samples:{" "}
                          {formatCount(
                            check.affected_samples
                          )}
                        </small>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
      </section>

      {/* ================================================================== */}
      {/* VALIDATION ISSUES                                                  */}
      {/* ================================================================== */}

      <DatasetValidationIssues
        issues={currentIssues}
        loading={validating}
        emptyMessage={
          validation
            ? "The latest validation run reported no issues."
            : "Run validation to see reported issues."
        }
      />

      {/* ================================================================== */}
      {/* VALIDATION FOOTER                                                  */}
      {/* ================================================================== */}

      {canManage && validation && (
        <div className="dataset-validation-page__footer">
          <div>
            <span>Validation run</span>

            <strong>
              {validation?.run?.id ??
                validation?.run_id ??
                "Completed"}
            </strong>
          </div>

          <button
            type="button"
            className="dataset-button dataset-button--primary"
            onClick={handleValidate}
            disabled={!canValidate}
          >
            <RefreshCw
              size={16}
              className={
                validating
                  ? "dataset-icon--spinning"
                  : ""
              }
            />

            {validating ? "Running..." : "Run Again"}
          </button>
        </div>
      )}
    </main>
  );
}
