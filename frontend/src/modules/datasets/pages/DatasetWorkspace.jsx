import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../../core/auth/AuthProvider";
import { AlertCircle, Database, RefreshCw } from "lucide-react";

import datasetService from "../services/datasetService";
import {
  createDefaultDatasetFilters,
  DATASET_FEATURES,
  WORKSPACE_PAGE_SIZE,
} from "../types";

import "../styles/datasets.css";

import DatasetStats from "../components/DatasetStats";
import DatasetFilters from "../components/DatasetFilters";
import DatasetTable from "../components/DatasetTable";
import DatasetSelectionBar from "../components/DatasetSelectionBar";
import DatasetDetailsDrawer from "../components/DatasetDetailsDrawer";
import DatasetCreateModal from "../components/DatasetCreateModal";

const EMPTY_SUMMARY = {
  total_emails: 0,
  normal_count: 0,
  bombing_count: 0,
};

function getItems(response) {
  if (Array.isArray(response)) {
    return response;
  }

  const items =
    response?.items ??
    response?.emails ??
    response?.results ??
    response?.data?.items ??
    response?.data?.emails ??
    response?.data?.results;

  return Array.isArray(items) ? items : [];
}

function getTotal(response, items) {
  const value =
    response?.total ??
    response?.total_count ??
    response?.pagination?.total ??
    response?.data?.total ??
    response?.data?.total_count ??
    response?.data?.pagination?.total;

  if (value !== undefined && value !== null && Number.isFinite(Number(value))) {
    return Number(value);
  }

  return items.length;
}

function getGroundTruth(email) {
  const value = String(
    email?.ground_truth ??
      email?.label ??
      email?.classification ??
      ""
  )
    .trim()
    .toLowerCase();

  if (["normal", "ham", "0"].includes(value)) {
    return "normal";
  }

  if (
    ["bomb", "bombing", "email_bomb", "email-bomb", "1"].includes(value)
  ) {
    return "bombing";
  }

  return "unknown";
}

function getEmailSummary(items, total) {
  const counts = items.reduce(
    (result, email) => {
      const label = getGroundTruth(email);

      if (label === "normal") {
        result.normal_count += 1;
      } else if (label === "bombing") {
        result.bombing_count += 1;
      }

      return result;
    },
    {
      normal_count: 0,
      bombing_count: 0,
    }
  );

  return {
    total_emails: Number(total) || items.length,
    normal_count: counts.normal_count,
    bombing_count: counts.bombing_count,
  };
}

function getSummary(response, items, total) {
  const summary =
    response?.summary ??
    response?.stats ??
    response?.data?.summary ??
    response?.data?.stats ??
    response?.data?.data?.summary ??
    {};

  const hasSummary =
    summary.total_emails !== undefined ||
    summary.dataset_emails !== undefined ||
    summary.total !== undefined ||
    summary.normal_count !== undefined ||
    summary.normal !== undefined ||
    summary.bombing_count !== undefined ||
    summary.bombing !== undefined;

  if (!hasSummary) {
    return getEmailSummary(items, total);
  }

  const normalCount = Number(
    summary.normal_count ??
      summary.normal ??
      summary.normal_emails ??
      0
  );

  const bombingCount = Number(
    summary.bombing_count ??
      summary.bombing ??
      summary.bombing_emails ??
      0
  );

  const totalEmails = Number(
    summary.total_emails ??
      summary.dataset_emails ??
      summary.total ??
      total ??
      items.length
  );

  return {
    total_emails: Number.isFinite(totalEmails) ? totalEmails : items.length,
    normal_count: Number.isFinite(normalCount) ? normalCount : 0,
    bombing_count: Number.isFinite(bombingCount) ? bombingCount : 0,
  };
}

function getEmailId(email) {
  return email?.email_id ?? email?.id ?? email?.message_id ?? null;
}

function getErrorMessage(error, fallback) {
  return (
    error?.response?.data?.detail ??
    error?.detail ??
    error?.message ??
    fallback
  );
}

function getResponseData(response) {
  return (
    response?.email ??
    response?.data?.email ??
    response?.data?.data ??
    response?.data ??
    response
  );
}

export default function DatasetWorkspace() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);
  const [filters, setFilters] = useState(createDefaultDatasetFilters);
  const [page, setPage] = useState(1);

  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedIds, setSelectedIds] = useState([]);
  const [allMatching, setAllMatching] = useState(false);
  const [selectionLoading, setSelectionLoading] = useState(false);

  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const pageSize = WORKSPACE_PAGE_SIZE || 30;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const selectedCount = selectedIds.length;

  const featureSchema = DATASET_FEATURES;

  const selectedEmails = useMemo(() => {
    const selectedSet = new Set(selectedIds.map(String));

    return items.filter((item) =>
      selectedSet.has(String(getEmailId(item)))
    );
  }, [items, selectedIds]);

  const normalCount = useMemo(
    () =>
      selectedEmails.filter(
        (email) => getGroundTruth(email) === "normal"
      ).length,
    [selectedEmails]
  );

  const bombingCount = useMemo(
    () =>
      selectedEmails.filter(
        (email) => getGroundTruth(email) === "bombing"
      ).length,
    [selectedEmails]
  );

  const loadWorkspace = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await datasetService.getWorkspace({
        filters,
        page,
        page_size: pageSize,
      });

      const nextItems = getItems(response);
      const nextTotal = getTotal(response, nextItems);
      const nextSummary = getSummary(response, nextItems, nextTotal);

      setItems(nextItems);
      setTotal(nextTotal);
      setSummary(nextSummary);
    } catch (err) {
      setItems([]);
      setTotal(0);
      setSummary(EMPTY_SUMMARY);

      setError(
        getErrorMessage(
          err,
          "Unable to load the dataset workspace."
        )
      );
    } finally {
      setLoading(false);
    }
  }, [filters, page, pageSize]);

  useEffect(() => {
    loadWorkspace();
  }, [loadWorkspace]);

  const handleFiltersChange = useCallback((nextFilters) => {
    setFilters(nextFilters);
    setPage(1);
    setSelectedIds([]);
    setAllMatching(false);
  }, []);

  const handleResetFilters = useCallback(() => {
    setFilters(createDefaultDatasetFilters());
    setPage(1);
    setSelectedIds([]);
    setAllMatching(false);
  }, []);

  const handleSelectionChange = useCallback((nextIds) => {
    setSelectedIds(Array.isArray(nextIds) ? nextIds : []);
    setAllMatching(false);
  }, []);

  const handleSelectAllMatching = useCallback(async () => {
    if (selectionLoading || total === 0) {
      return;
    }

    setSelectionLoading(true);
    setError("");

    try {
      const response = await datasetService.selectAllMatching({
        filters,
      });

      const ids =
        response?.email_ids ??
        response?.selected_ids ??
        response?.ids ??
        response?.data?.email_ids ??
        response?.data?.selected_ids ??
        response?.data?.ids ??
        [];

      if (!Array.isArray(ids)) {
        throw new Error(
          "The selection API did not return an email ID list."
        );
      }

      setSelectedIds(ids);
      setAllMatching(true);
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Unable to select all matching emails."
        )
      );
    } finally {
      setSelectionLoading(false);
    }
  }, [filters, selectionLoading, total]);

  const handleClearSelection = useCallback(() => {
    setSelectedIds([]);
    setAllMatching(false);
  }, []);

  const handleViewEmail = useCallback(async (email) => {
    const emailId = getEmailId(email);

    setDetailsOpen(true);
    setSelectedEmail(email);
    setDetailsError("");

    if (!emailId) {
      setDetailsError("Email ID is missing.");
      return;
    }

    setDetailsLoading(true);

    try {
      const response = await datasetService.getWorkspaceEmail(emailId);
      setSelectedEmail(getResponseData(response));
    } catch (err) {
      setDetailsError(
        getErrorMessage(
          err,
          "Unable to load email details."
        )
      );
    } finally {
      setDetailsLoading(false);
    }
  }, []);

  const handleCloseDetails = useCallback(() => {
    setDetailsOpen(false);
    setSelectedEmail(null);
    setDetailsError("");
    setDetailsLoading(false);
  }, []);

  const handleOpenCreateModal = useCallback(() => {
    setCreateError("");
    setCreateModalOpen(true);
  }, []);

  const handleCloseCreateModal = useCallback(() => {
    if (creating) {
      return;
    }

    setCreateModalOpen(false);
    setCreateError("");
  }, [creating]);

  const handleCreateDataset = useCallback(
    async (payload) => {
      if (selectedIds.length === 0) {
        setCreateError("Select at least one email.");
        return;
      }

      setCreating(true);
      setCreateError("");

      try {
        await datasetService.createDataset({
          ...payload,
          email_ids: selectedIds,
        });

        setCreateModalOpen(false);
        setSelectedIds([]);
        setAllMatching(false);

        await loadWorkspace();
      } catch (err) {
        setCreateError(
          getErrorMessage(
            err,
            "Unable to create the dataset."
          )
        );
      } finally {
        setCreating(false);
      }
    },
    [selectedIds, loadWorkspace]
  );

  return (
    <main className="dataset-workspace">
      <header className="dataset-page-header">
        <div className="dataset-page-header__title">
          <div className="dataset-page-header__icon">
            <Database size={22} aria-hidden="true" />
          </div>

          <div>
            <h1>Dataset Workspace</h1>
            <p>
              Browse eligible emails and create datasets for machine
              learning experiments.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="dataset-button dataset-button--secondary"
          onClick={loadWorkspace}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "dataset-icon--spinning" : ""}
          />
          Refresh
        </button>
      </header>

      <DatasetStats
        summary={summary}
        loading={loading}
      />

      <DatasetFilters
        filters={filters}
        onChange={handleFiltersChange}
        onReset={handleResetFilters}
        disabled={loading}
      />

      {error && (
        <div className="dataset-workspace__error" role="alert">
          <AlertCircle size={18} />

          <span>{error}</span>

          <button
            type="button"
            className="dataset-button dataset-button--ghost"
            onClick={loadWorkspace}
            disabled={loading}
          >
            Retry
          </button>
        </div>
      )}

      {canManage && <DatasetSelectionBar
        selectedCount={selectedCount}
        totalMatching={total}
        allMatching={allMatching}
        loading={selectionLoading}
        disabled={loading}
        canManage={canManage}
        onSelectAllMatching={handleSelectAllMatching}
        onClearSelection={handleClearSelection}
        onCreateDataset={handleOpenCreateModal}
      />}

      <DatasetTable
        canSelect={canManage}
        items={items}
        selectedIds={selectedIds}
        onSelectionChange={handleSelectionChange}
        onView={handleViewEmail}
        page={page}
        pageSize={pageSize}
        total={total}
        totalPages={totalPages}
        onPageChange={setPage}
        loading={loading}
        disabled={selectionLoading}
      />

      <DatasetDetailsDrawer
        open={detailsOpen}
        email={selectedEmail}
        loading={detailsLoading}
        error={detailsError}
        onClose={handleCloseDetails}
      />

      {canManage && <DatasetCreateModal
        open={createModalOpen}
        selectedCount={selectedCount}
        normalCount={normalCount}
        bombingCount={bombingCount}
        featureSchema={featureSchema}
        submitting={creating}
        error={createError}
        onClose={handleCloseCreateModal}
        onSubmit={handleCreateDataset}
      />}
    </main>
  );
}
