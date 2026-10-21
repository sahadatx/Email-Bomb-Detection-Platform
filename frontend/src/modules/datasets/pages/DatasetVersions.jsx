import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useAuth } from "../../../core/auth/AuthProvider";

import {
  GitBranch,
  RefreshCw,
  Plus,
  AlertCircle,
  Database,
} from "lucide-react";

import "../styles/datasets.css";

import datasetService from "../services/datasetService";
import { WORKSPACE_PAGE_SIZE } from "../types";

import DatasetVersionTable from "../components/DatasetVersionTable";
import DatasetVersionModal from "../components/DatasetVersionModal";
import DatasetVersionDrawer from "../components/DatasetVersionDrawer";

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

const DEFAULT_PAGE_SIZE = 30;

/* -------------------------------------------------------------------------- */
/* Response Helpers                                                           */
/* -------------------------------------------------------------------------- */

function getItems(response) {
  if (Array.isArray(response)) {
    return response;
  }

  const candidates = [
    response?.items,
    response?.versions,
    response?.results,
    response?.data?.items,
    response?.data?.versions,
    response?.data?.results,
  ];

  return candidates.find(Array.isArray) ?? [];
}

function getTotal(response, items) {
  const candidates = [
    response?.pagination?.total,
    response?.total,
    response?.total_count,
    response?.data?.pagination?.total,
    response?.data?.total,
    response?.data?.total_count,
  ];

  const value = candidates.find(
    (candidate) =>
      candidate !== null && candidate !== undefined
  );

  const total = Number(value);

  return Number.isFinite(total) && total >= 0
    ? total
    : items.length;
}

function getTotalPages(response) {
  const candidates = [
    response?.pagination?.total_pages,
    response?.total_pages,
    response?.data?.pagination?.total_pages,
    response?.data?.total_pages,
  ];

  const value = candidates.find(
    (candidate) =>
      candidate !== null && candidate !== undefined
  );

  const totalPages = Number(value);

  return Number.isInteger(totalPages) && totalPages > 0
    ? totalPages
    : 1;
}

function getErrorMessage(error, fallback) {
  const responseData = error?.response?.data;

  const detail =
    responseData?.detail ??
    responseData?.message ??
    responseData?.error?.message ??
    responseData?.error?.details ??
    error?.detail ??
    error?.message;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const location = Array.isArray(item?.loc)
          ? item.loc.join(".")
          : "";

        const message = item?.msg ?? String(item);

        return location
          ? `${location}: ${message}`
          : message;
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return fallback;
}

/* -------------------------------------------------------------------------- */
/* Dataset Helpers                                                            */
/* -------------------------------------------------------------------------- */

function getDatasetId(dataset) {
  return dataset?.dataset_id ?? dataset?.id ?? "";
}

function getDatasetName(dataset) {
  return (
    dataset?.name ??
    dataset?.dataset_name ??
    "Unnamed Dataset"
  );
}

/* -------------------------------------------------------------------------- */
/* Version Helpers                                                            */
/* -------------------------------------------------------------------------- */

function getVersionId(version) {
  return version?.version_id ?? version?.id ?? "";
}

function getVersionDetails(response) {
  return (
    response?.version ??
    response?.data?.version ??
    response?.data ??
    response
  );
}

function getVersionTimestamp(version) {
  const value =
    version?.created_at ??
    version?.validated_at ??
    null;

  if (!value) {
    return 0;
  }

  const timestamp = new Date(value).getTime();

  return Number.isFinite(timestamp) ? timestamp : 0;
}

/* -------------------------------------------------------------------------- */
/* Fetch All Versions For One Dataset                                         */
/* -------------------------------------------------------------------------- */

/**
 * Fetch every page of versions for one dataset.
 *
 * The API is dataset-specific, so this helper requests page 1 first
 * and then loads the remaining pages using the returned pagination.
 */
async function fetchAllVersionsForDataset(datasetId, pageSize) {
  const firstResponse = await datasetService.listVersions({
    dataset_id: datasetId,
    page: 1,
    page_size: pageSize,
  });

  const firstItems = getItems(firstResponse);
  const totalPages = getTotalPages(firstResponse);

  if (totalPages <= 1) {
    return firstItems;
  }

  const remainingPages = await Promise.all(
    Array.from(
      { length: totalPages - 1 },
      (_, index) =>
        datasetService.listVersions({
          dataset_id: datasetId,
          page: index + 2,
          page_size: pageSize,
        })
    )
  );

  return [
    ...firstItems,
    ...remainingPages.flatMap(getItems),
  ];
}

/* -------------------------------------------------------------------------- */
/* Dataset Versions Page                                                      */
/* -------------------------------------------------------------------------- */

export default function DatasetVersions() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);
  /* ------------------------------------------------------------------------ */
  /* State                                                                    */
  /* ------------------------------------------------------------------------ */

  const [datasets, setDatasets] = useState([]);
  const [versions, setVersions] = useState([]);

  const [selectedDatasetId, setSelectedDatasetId] = useState("");

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [creatingVersion, setCreatingVersion] = useState(false);

  const [error, setError] = useState("");
  const [createVersionError, setCreateVersionError] = useState("");

  const [versionModalOpen, setVersionModalOpen] = useState(false);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  /*
   * Request counters prevent stale API responses from updating state.
   */
  const datasetsRequestRef = useRef(0);
  const versionsRequestRef = useRef(0);
  const detailsRequestRef = useRef(0);

  /* ------------------------------------------------------------------------ */
  /* Derived State                                                            */
  /* ------------------------------------------------------------------------ */

  const pageSize =
    Number(WORKSPACE_PAGE_SIZE) > 0
      ? Number(WORKSPACE_PAGE_SIZE)
      : DEFAULT_PAGE_SIZE;

  const isAllDatasets = !selectedDatasetId;

  const totalPages = Math.max(
    1,
    Math.ceil(total / pageSize)
  );

  const selectedDataset = useMemo(
    () =>
      datasets.find(
        (dataset) =>
          String(getDatasetId(dataset)) ===
          String(selectedDatasetId)
      ) ?? null,
    [datasets, selectedDatasetId]
  );

  /*
   * When no dataset is selected, versions contains all versions.
   * Pagination is therefore performed on the frontend.
   *
   * When a dataset is selected, the API already returns one page.
   */
  const visibleVersions = useMemo(() => {
    if (!isAllDatasets) {
      return versions;
    }

    const startIndex = (page - 1) * pageSize;

    return versions.slice(
      startIndex,
      startIndex + pageSize
    );
  }, [versions, isAllDatasets, page, pageSize]);

  /* ------------------------------------------------------------------------ */
  /* Load Datasets                                                            */
  /* ------------------------------------------------------------------------ */

  const loadDatasets = useCallback(async () => {
    const requestId = ++datasetsRequestRef.current;

    setDatasetsLoading(true);

    try {
      const response = await datasetService.listDatasets({
        page: 1,
        page_size: DEFAULT_PAGE_SIZE,
      });

      const nextDatasets = getItems(response);

      if (requestId !== datasetsRequestRef.current) {
        return nextDatasets;
      }

      setDatasets(nextDatasets);

      setSelectedDatasetId((currentId) => {
        if (!currentId) {
          return currentId;
        }

        const stillExists = nextDatasets.some(
          (dataset) =>
            String(getDatasetId(dataset)) ===
            String(currentId)
        );

        return stillExists ? currentId : "";
      });

      return nextDatasets;
    } catch (err) {
      if (requestId !== datasetsRequestRef.current) {
        return [];
      }

      setDatasets([]);
      setSelectedDatasetId("");

      setError(
        getErrorMessage(
          err,
          "Unable to load datasets."
        )
      );

      return [];
    } finally {
      if (requestId === datasetsRequestRef.current) {
        setDatasetsLoading(false);
      }
    }
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Load All Dataset Versions                                                */
  /* ------------------------------------------------------------------------ */

  const loadAllVersions = useCallback(
    async (datasetList) => {
      const requestId = ++versionsRequestRef.current;

      setLoading(true);
      setError("");
      setVersions([]);
      setTotal(0);

      if (!Array.isArray(datasetList) || datasetList.length === 0) {
        setLoading(false);
        return [];
      }

      try {
        /*
         * Fetch every dataset's versions independently.
         * A failed request rejects the operation so the page can
         * display an error instead of silently showing incomplete data.
         */
        const datasetResults = await Promise.all(
          datasetList.map(async (dataset) => {
            const datasetId = getDatasetId(dataset);

            if (!datasetId) {
              return [];
            }

            return fetchAllVersionsForDataset(
              datasetId,
              pageSize
            );
          })
        );

        const allVersions = datasetResults
          .flat()
          .sort(
            (a, b) =>
              getVersionTimestamp(b) -
              getVersionTimestamp(a)
          );

        if (requestId !== versionsRequestRef.current) {
          return allVersions;
        }

        setVersions(allVersions);
        setTotal(allVersions.length);

        return allVersions;
      } catch (err) {
        if (requestId !== versionsRequestRef.current) {
          return [];
        }

        setVersions([]);
        setTotal(0);

        setError(
          getErrorMessage(
            err,
            "Unable to load all dataset versions."
          )
        );

        return [];
      } finally {
        if (requestId === versionsRequestRef.current) {
          setLoading(false);
        }
      }
    },
    [pageSize]
  );

  /* ------------------------------------------------------------------------ */
  /* Load Selected Dataset Versions                                           */
  /* ------------------------------------------------------------------------ */

  const loadSelectedDatasetVersions = useCallback(
    async (datasetId, pageNumber) => {
      const requestId = ++versionsRequestRef.current;

      if (!datasetId) {
        return [];
      }

      setLoading(true);
      setError("");

      try {
        const response = await datasetService.listVersions({
          dataset_id: datasetId,
          page: pageNumber,
          page_size: pageSize,
        });

        const nextVersions = getItems(response);
        const nextTotal = getTotal(response, nextVersions);

        if (requestId !== versionsRequestRef.current) {
          return nextVersions;
        }

        setVersions(nextVersions);
        setTotal(nextTotal);

        return nextVersions;
      } catch (err) {
        if (requestId !== versionsRequestRef.current) {
          return [];
        }

        setVersions([]);
        setTotal(0);

        setError(
          getErrorMessage(
            err,
            "Unable to load dataset versions."
          )
        );

        return [];
      } finally {
        if (requestId === versionsRequestRef.current) {
          setLoading(false);
        }
      }
    },
    [pageSize]
  );

  /* ------------------------------------------------------------------------ */
  /* Initial Dataset Loading                                                  */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    loadDatasets();

    return () => {
      datasetsRequestRef.current += 1;
    };
  }, [loadDatasets]);

  /* ------------------------------------------------------------------------ */
  /* Load Versions When Filter or Page Changes                                */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (datasetsLoading) {
      return undefined;
    }

    if (selectedDatasetId) {
      loadSelectedDatasetVersions(
        selectedDatasetId,
        page
      );
    } else {
      loadAllVersions(datasets);
    }

    return () => {
      versionsRequestRef.current += 1;
    };
  }, [
    datasetsLoading,
    datasets,
    selectedDatasetId,
    page,
    loadAllVersions,
    loadSelectedDatasetVersions,
  ]);

  /* ------------------------------------------------------------------------ */
  /* Dataset Filter                                                           */
  /* ------------------------------------------------------------------------ */

  const handleDatasetFilterChange = useCallback((event) => {
    const nextDatasetId = event.target.value;

    setSelectedDatasetId(nextDatasetId);
    setPage(1);

    setVersions([]);
    setTotal(0);
    setError("");

    detailsRequestRef.current += 1;
    setSelectedVersion(null);
    setDrawerOpen(false);
    setDetailsError("");
    setDetailsLoading(false);
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Create Version Modal                                                     */
  /* ------------------------------------------------------------------------ */

  const handleOpenCreateModal = useCallback(() => {
    setCreateVersionError("");
    setVersionModalOpen(true);
  }, []);

  const handleCloseCreateModal = useCallback(() => {
    if (creatingVersion) {
      return;
    }

    setVersionModalOpen(false);
    setCreateVersionError("");
  }, [creatingVersion]);

  /* ------------------------------------------------------------------------ */
  /* Create Version                                                           */
  /* ------------------------------------------------------------------------ */

  const handleCreateVersion = useCallback(
    async (payload) => {
      if (creatingVersion) {
        return;
      }

      setCreatingVersion(true);
      setCreateVersionError("");

      try {
        if (
          !payload ||
          typeof payload !== "object" ||
          !payload.dataset_id ||
          !String(payload.name ?? "").trim() ||
          !payload.split ||
          typeof payload.split !== "object"
        ) {
          throw new Error(
            "The version form returned an incomplete payload."
          );
        }

        const split = payload.split;

        const requestPayload = {
          dataset_id: payload.dataset_id,
          name: String(payload.name).trim(),
          split: {
            training_percentage: Number(
              split.training_percentage
            ),
            validation_percentage: Number(
              split.validation_percentage
            ),
            testing_percentage: Number(
              split.testing_percentage
            ),
            random_seed: Number(split.random_seed),
            stratified: split.stratified,
          },
        };

        const percentages = [
          requestPayload.split.training_percentage,
          requestPayload.split.validation_percentage,
          requestPayload.split.testing_percentage,
        ];

        const validPercentages = percentages.every(
          (value) =>
            Number.isInteger(value) &&
            value >= 0 &&
            value <= 100
        );

        const validSeed =
          Number.isInteger(requestPayload.split.random_seed) &&
          requestPayload.split.random_seed >= 0;

        const validStratified =
          typeof requestPayload.split.stratified === "boolean";

        if (
          !validPercentages ||
          percentages.reduce((sum, value) => sum + value, 0) !== 100 ||
          !validSeed ||
          !validStratified
        ) {
          throw new Error(
            "Invalid split configuration. Percentages must be whole numbers totaling 100, the random seed must be a non-negative integer, and stratified must be true or false."
          );
        }

        await datasetService.createVersion(requestPayload);

        const createdDatasetId = String(
          requestPayload.dataset_id
        );

        setVersionModalOpen(false);
        setCreateVersionError("");
        setPage(1);
        setSelectedDatasetId(createdDatasetId);

        /*
         * If the created version belongs to the currently selected
         * dataset and page 1 is already active, refresh directly.
         *
         * Otherwise, the effect will load the selected dataset.
         */
        if (
          String(selectedDatasetId) === createdDatasetId &&
          page === 1
        ) {
          await loadSelectedDatasetVersions(
            createdDatasetId,
            1
          );
        }
      } catch (err) {
        setCreateVersionError(
          getErrorMessage(
            err,
            "Unable to create dataset version."
          )
        );
      } finally {
        setCreatingVersion(false);
      }
    },
    [
      creatingVersion,
      selectedDatasetId,
      page,
      loadSelectedDatasetVersions,
    ]
  );

  /* ------------------------------------------------------------------------ */
  /* View Version Details                                                     */
  /* ------------------------------------------------------------------------ */

  const handleViewVersion = useCallback(async (version) => {
    const requestId = ++detailsRequestRef.current;
    const versionId = getVersionId(version);

    setDrawerOpen(true);
    setSelectedVersion(version);
    setDetailsError("");
    setDetailsLoading(false);

    if (!versionId) {
      setDetailsError("Version ID is missing.");
      return;
    }

    setDetailsLoading(true);

    try {
      const response = await datasetService.getVersion(
        versionId
      );

      if (requestId !== detailsRequestRef.current) {
        return;
      }

      setSelectedVersion(getVersionDetails(response));
    } catch (err) {
      if (requestId !== detailsRequestRef.current) {
        return;
      }

      setDetailsError(
        getErrorMessage(
          err,
          "Unable to load version details."
        )
      );
    } finally {
      if (requestId === detailsRequestRef.current) {
        setDetailsLoading(false);
      }
    }
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Close Details Drawer                                                     */
  /* ------------------------------------------------------------------------ */

  const handleCloseDrawer = useCallback(() => {
    detailsRequestRef.current += 1;

    setDrawerOpen(false);
    setSelectedVersion(null);
    setDetailsError("");
    setDetailsLoading(false);
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Refresh                                                                  */
  /* ------------------------------------------------------------------------ */

  const handleRefresh = useCallback(async () => {
    if (refreshing) {
      return;
    }

    setRefreshing(true);
    setError("");

    try {
      const nextDatasets = await loadDatasets();

      /*
       * Load versions using the refreshed dataset list.
       * In all-datasets mode, this refreshes every dataset.
       */
      if (!selectedDatasetId) {
        await loadAllVersions(nextDatasets);
      } else {
        const stillExists = nextDatasets.some(
          (dataset) =>
            String(getDatasetId(dataset)) ===
            String(selectedDatasetId)
        );

        if (stillExists) {
          await loadSelectedDatasetVersions(
            selectedDatasetId,
            page
          );
        } else {
          await loadAllVersions(nextDatasets);
        }
      }
    } finally {
      setRefreshing(false);
    }
  }, [
    refreshing,
    loadDatasets,
    loadAllVersions,
    loadSelectedDatasetVersions,
    selectedDatasetId,
    page,
  ]);

  /* ------------------------------------------------------------------------ */
  /* Retry                                                                    */
  /* ------------------------------------------------------------------------ */

  const handleRetry = useCallback(() => {
    if (selectedDatasetId) {
      loadSelectedDatasetVersions(
        selectedDatasetId,
        page
      );
    } else {
      loadAllVersions(datasets);
    }
  }, [
    selectedDatasetId,
    page,
    datasets,
    loadSelectedDatasetVersions,
    loadAllVersions,
  ]);

  /* ------------------------------------------------------------------------ */
  /* Pagination                                                               */
  /* ------------------------------------------------------------------------ */

  const handlePageChange = useCallback(
    (nextPage) => {
      const normalizedPage = Number(nextPage);

      if (
        !Number.isInteger(normalizedPage) ||
        normalizedPage < 1 ||
        normalizedPage > totalPages
      ) {
        return;
      }

      setPage(normalizedPage);
    },
    [totalPages]
  );

  /* ------------------------------------------------------------------------ */
  /* Render                                                                   */
  /* ------------------------------------------------------------------------ */

  return (
    <main className="dataset-versions-page">
      {/* Page Header */}
      <header className="dataset-page-header">
        <div className="dataset-page-header__title">
          <div className="dataset-page-header__icon">
            <GitBranch size={22} />
          </div>

          <div>
            <h1>Dataset Versions</h1>
            <p>
              Create and manage immutable dataset versions
              and their train, validation, and test splits.
            </p>
          </div>
        </div>

        <div className="dataset-versions-page__header-actions">
          <button
            type="button"
            className="dataset-button dataset-button--secondary"
            onClick={handleRefresh}
            disabled={refreshing || datasetsLoading}
          >
            <RefreshCw
              size={16}
              className={
                refreshing || loading || datasetsLoading
                  ? "dataset-icon--spinning"
                  : ""
              }
            />
            Refresh
          </button>

          {canManage && <button
            type="button"
            className="dataset-button dataset-button--primary"
            onClick={handleOpenCreateModal}
            disabled={
              datasetsLoading ||
              datasets.length === 0 ||
              creatingVersion
            }
          >
            <Plus size={16} />
            Create Version
          </button>}
        </div>
      </header>

      {/* Dataset Filter and Summary */}
      <section className="dataset-versions-page__toolbar">
        <div className="dataset-form-field dataset-versions-page__filter">
          <label htmlFor="versions-dataset-filter">
            Filter by Dataset
          </label>

          <select
            id="versions-dataset-filter"
            value={selectedDatasetId}
            onChange={handleDatasetFilterChange}
            disabled={datasetsLoading}
          >
            <option value="">
              All Datasets
            </option>

            {datasets.map((dataset) => {
              const id = getDatasetId(dataset);

              return (
                <option key={id} value={id}>
                  {getDatasetName(dataset)}
                </option>
              );
            })}
          </select>
        </div>

        <div className="dataset-versions-page__summary">
          <span>
            {total.toLocaleString()}{" "}
            {total === 1 ? "version" : "versions"}
          </span>

          {selectedDataset ? (
            <span>
              Dataset:{" "}
              <strong>
                {getDatasetName(selectedDataset)}
              </strong>
            </span>
          ) : (
            <span>
              Showing versions from all datasets
            </span>
          )}
        </div>
      </section>

      {/* Page Error */}
      {error && (
        <div
          className="dataset-workspace__error"
          role="alert"
        >
          <AlertCircle size={18} />
          <span>{error}</span>

          <button
            type="button"
            className="dataset-button dataset-button--ghost"
            onClick={handleRetry}
            disabled={loading || datasetsLoading}
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty Dataset State */}
      {!datasetsLoading &&
        datasets.length === 0 &&
        !error && (
          <div className="dataset-versions-page__notice">
            <Database size={20} />

            <div>
              <strong>No datasets available</strong>
              <p>
                Create a dataset in Dataset Workspace
                before creating its first version.
              </p>
            </div>
          </div>
        )}

      {/* Versions Table */}
      {(datasetsLoading || datasets.length > 0) && (
        <DatasetVersionTable
          items={visibleVersions}
          datasets={datasets}
          loading={datasetsLoading || loading}
          error={error}
          page={page}
          pageSize={pageSize}
          total={total}
          totalPages={totalPages}
          onPageChange={handlePageChange}
          onView={handleViewVersion}
        />
      )}

      {/* Create Version Modal */}
      {canManage && <DatasetVersionModal
        open={versionModalOpen}
        className="dataset-version-modal--drawer"
        datasets={datasets}
        initialDatasetId={selectedDatasetId}
        submitting={creatingVersion}
        error={createVersionError}
        onClose={handleCloseCreateModal}
        onSubmit={handleCreateVersion}
      />}

      {/* Version Details Drawer */}
      <DatasetVersionDrawer
        open={drawerOpen}
        version={selectedVersion}
        datasets={datasets}
        loading={detailsLoading}
        error={detailsError}
        onClose={handleCloseDrawer}
      />
    </main>
  );
}
