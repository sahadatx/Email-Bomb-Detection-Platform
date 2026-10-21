import { useCallback, useEffect, useState } from "react";
import { Database, RefreshCw, Search, X } from "lucide-react";

import datasetService from "../services/datasetService";
import { WORKSPACE_PAGE_SIZE } from "../types";
import DatasetListTable from "../components/DatasetListTable";
import DatasetInfoDrawer from "../components/DatasetInfoDrawer";
import "../styles/datasets.css";

function getItems(response) {
  if (Array.isArray(response)) {
    return response;
  }

  const items =
    response?.items ??
    response?.datasets ??
    response?.results ??
    response?.data?.items ??
    response?.data?.datasets ??
    response?.data?.results;

  return Array.isArray(items) ? items : [];
}

function getTotal(response, items) {
  const value =
    response?.total ??
    response?.total_count ??
    response?.pagination?.total ??
    response?.pagination?.total_count ??
    response?.data?.total ??
    response?.data?.total_count ??
    response?.data?.pagination?.total;

  if (value !== undefined && value !== null && Number.isFinite(Number(value))) {
    return Math.max(0, Number(value));
  }

  return items.length;
}

function getErrorMessage(error) {
  const detail =
    error?.response?.data?.detail ??
    error?.detail ??
    error?.message;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg ?? String(item))
      .join(", ");
  }

  return "Unable to load datasets. Please try again.";
}

function getDatasetId(dataset) {
  return dataset?.dataset_id ?? dataset?.id ?? null;
}

function unwrapDataset(response) {
  return (
    response?.dataset ??
    response?.data?.dataset ??
    response?.data ??
    response
  );
}

export default function DatasetList() {
  const pageSize = WORKSPACE_PAGE_SIZE || 30;

  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedDataset, setSelectedDataset] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const loadDatasets = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await datasetService.listDatasets({
        search: appliedSearch || undefined,
        page,
        page_size: pageSize,
      });

      const datasets = getItems(response);

      setItems(datasets);
      setTotal(getTotal(response, datasets));
    } catch (err) {
      setItems([]);
      setTotal(0);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [appliedSearch, page, pageSize]);

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  const handleSearch = (event) => {
    event.preventDefault();

    const nextSearch = search.trim();

    if (nextSearch === appliedSearch) {
      if (page !== 1) {
        setPage(1);
      } else {
        loadDatasets();
      }
      return;
    }

    setPage(1);
    setAppliedSearch(nextSearch);
  };

  const handleClearSearch = () => {
    setSearch("");
    setAppliedSearch("");
    setPage(1);
  };

  const handlePageChange = (nextPage) => {
    const pageNumber = Number(nextPage);

    if (
      !Number.isInteger(pageNumber) ||
      pageNumber < 1 ||
      pageNumber > totalPages ||
      pageNumber === page
    ) {
      return;
    }

    setPage(pageNumber);
  };

  const handleViewDataset = async (dataset) => {
    const datasetId = getDatasetId(dataset);

    if (!datasetId) {
      setError("Dataset ID is missing. Unable to open details.");
      return;
    }

    setSelectedDataset(dataset);
    setDetailsOpen(true);
    setDetailsLoading(true);
    setDetailsError("");

    try {
      const response = await datasetService.getDataset(datasetId);
      const fullDataset = unwrapDataset(response);

      if (!fullDataset || typeof fullDataset !== "object") {
        throw new Error("The server returned an invalid dataset response.");
      }

      setSelectedDataset(fullDataset);
    } catch (err) {
      setDetailsError(getErrorMessage(err));
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setDetailsError("");
  };

  return (
    <main className="dataset-list-page">
      <header className="dataset-page-header">
        <div className="dataset-page-header__title">
          <div className="dataset-page-header__icon">
            <Database size={22} aria-hidden="true" />
          </div>

          <div>
            <h1>Datasets</h1>
            <p>
              View and manage datasets created from the Dataset Workspace.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="dataset-button dataset-button--secondary"
          onClick={loadDatasets}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "dataset-icon--spinning" : ""}
            aria-hidden="true"
          />
          Refresh
        </button>
      </header>

      <section className="dataset-list-page__toolbar">
        <form
          className="dataset-list-search"
          onSubmit={handleSearch}
          role="search"
        >
          <Search size={17} aria-hidden="true" />

          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search datasets..."
            aria-label="Search datasets"
          />

          {search && (
            <button
              type="button"
              className="dataset-icon-button"
              onClick={handleClearSearch}
              aria-label="Clear search"
              disabled={loading}
            >
              <X size={16} aria-hidden="true" />
            </button>
          )}

          <button
            type="submit"
            className="dataset-button dataset-button--primary"
            disabled={loading}
          >
            Search
          </button>
        </form>

        <span className="dataset-list-page__result-count">
          {total.toLocaleString()} datasets
        </span>
      </section>

      {error && (
        <div className="dataset-workspace__error" role="alert">
          <span>{error}</span>

          <button
            type="button"
            className="dataset-button dataset-button--ghost"
            onClick={loadDatasets}
            disabled={loading}
          >
            Retry
          </button>
        </div>
      )}

      <DatasetListTable
        items={items}
        loading={loading}
        error=""
        page={page}
        pageSize={pageSize}
        total={total}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        onView={handleViewDataset}
      />

      <DatasetInfoDrawer
        open={detailsOpen}
        dataset={selectedDataset}
        loading={detailsLoading}
        error={detailsError}
        onClose={handleCloseDetails}
      />
    </main>
  );
}