
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  X,
  Database,
  FileText,
  Layers,
  Mail,
  ShieldCheck,
  AlertTriangle,
  Search,
  Plus,
  Trash2,
  Pencil,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  LoaderCircle,
  Check,
  Inbox,
} from "lucide-react";

import datasetService from "../services/datasetService";

const PAGE_SIZE = 10;
const ELIGIBLE_PAGE_SIZE = 100;

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatValue(value) {
  if (value === undefined || value === null || value === "") {
    return "—";
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  return String(value);
}

function getStatusClass(status) {
  const normalized = String(status ?? "unknown")
    .trim()
    .toLowerCase()
    .replaceAll("_", "-");

  return `dataset-label--${normalized}`;
}

function DetailField({ label, value, code = false }) {
  return (
    <div className="dataset-details-field">
      <span>{label}</span>
      {code ? (
        <code>{formatValue(value)}</code>
      ) : (
        <strong>{formatValue(value)}</strong>
      )}
    </div>
  );
}

function getErrorMessage(error, fallback) {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    fallback
  );
}

function normalizeItems(response) {
  if (Array.isArray(response)) return response;
  if (Array.isArray(response?.items)) return response.items;
  if (Array.isArray(response?.data?.items)) return response.data.items;
  return [];
}

function getPagination(response, itemCount, page, pageSize) {
  const pagination =
    response?.pagination ||
    response?.data?.pagination ||
    {};

  const total = Number(pagination.total ?? itemCount);
  const totalPages = Number(
    pagination.total_pages ??
      Math.ceil(total / pageSize)
  );

  return {
    page: Number(pagination.page ?? page),
    pageSize: Number(pagination.page_size ?? pageSize),
    total,
    totalPages,
  };
}

function Modal({ title, onClose, children, wide = false }) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") onClose?.();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="dataset-drawer-backdrop dataset-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose?.();
        }
      }}
    >
      <section
        className={`dataset-modal ${wide ? "dataset-modal--wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header className="dataset-modal__header">
          <h3>{title}</h3>
          <button
            type="button"
            className="dataset-icon-button"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={19} />
          </button>
        </header>
        <div className="dataset-modal__body">{children}</div>
      </section>
    </div>
  );
}

function LoadingState({ message = "Loading..." }) {
  return (
    <div className="dataset-details-drawer__state" role="status">
      <LoaderCircle className="dataset-spinner" size={24} />
      <p>{message}</p>
    </div>
  );
}

export default function DatasetInfoDrawer({
  open = false,
  dataset = null,
  loading = false,
  error = "",
  onClose,
  onDatasetUpdated,
}) {
  const [emails, setEmails] = useState([]);
  const [emailPagination, setEmailPagination] = useState({
    page: 1,
    pageSize: PAGE_SIZE,
    total: 0,
    totalPages: 0,
  });
  const [emailSearch, setEmailSearch] = useState("");
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [emailPage, setEmailPage] = useState(1);

  const [selectedEmailIds, setSelectedEmailIds] = useState([]);
  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [removeLoading, setRemoveLoading] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [operationError, setOperationError] = useState("");
  const [operationMessage, setOperationMessage] = useState("");

  const [eligibleEmails, setEligibleEmails] = useState([]);
  const [eligibleLoading, setEligibleLoading] = useState(false);
  const [eligibleError, setEligibleError] = useState("");
  const [eligibleSearch, setEligibleSearch] = useState("");
  const [eligiblePage, setEligiblePage] = useState(1);
  const [eligibleTotalPages, setEligibleTotalPages] = useState(0);
  const [eligibleTotal, setEligibleTotal] = useState(0);
  const [selectedEligibleIds, setSelectedEligibleIds] = useState([]);

  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const datasetId = dataset?.id;

  const loadDatasetEmails = useCallback(async () => {
    if (!datasetId) {
      setEmails([]);
      setEmailPagination({
        page: 1,
        pageSize: PAGE_SIZE,
        total: 0,
        totalPages: 0,
      });
      return;
    }

    setEmailLoading(true);
    setEmailError("");

    try {
      const response = await datasetService.getDatasetEmails(
        datasetId,
        {
          page: emailPage,
          page_size: PAGE_SIZE,
          search: emailSearch.trim() || undefined,
        }
      );

      const items = normalizeItems(response);
      setEmails(items);
      setEmailPagination(
        getPagination(response, items.length, emailPage, PAGE_SIZE)
      );

      setSelectedEmailIds((previous) =>
        previous.filter((id) =>
          items.some((item) => item.email_id === id)
        )
      );
    } catch (err) {
      setEmailError(
        getErrorMessage(err, "Failed to load dataset emails.")
      );
      setEmails([]);
    } finally {
      setEmailLoading(false);
    }
  }, [datasetId, emailPage, emailSearch]);

  useEffect(() => {
    if (!open || !datasetId) return;
    loadDatasetEmails();
  }, [open, datasetId, loadDatasetEmails]);

  useEffect(() => {
    if (!open) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === "Escape" && !addOpen && !editOpen) {
        onClose?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, addOpen, editOpen, onClose]);

  useEffect(() => {
    if (!dataset) return;
    setEditName(dataset.name ?? "");
    setEditDescription(dataset.description ?? "");
  }, [dataset]);

  useEffect(() => {
    setEmailPage(1);
    setSelectedEmailIds([]);
    setOperationError("");
    setOperationMessage("");
  }, [datasetId]);

  const loadEligibleEmails = useCallback(async () => {
    if (!datasetId) return;

    setEligibleLoading(true);
    setEligibleError("");

    try {
      // Workspace returns Dataset-eligible, feature-extracted emails.
      // Load all workspace pages so existing memberships can be
      // excluded reliably, not just those on the current page.
      const firstResponse = await datasetService.getWorkspace({
        page: 1,
        page_size: ELIGIBLE_PAGE_SIZE,
      });

      const firstItems = normalizeItems(firstResponse);
      const firstPagination = getPagination(
        firstResponse,
        firstItems.length,
        1,
        ELIGIBLE_PAGE_SIZE
      );

      let allItems = [...firstItems];

      for (let page = 2; page <= firstPagination.totalPages; page += 1) {
        const response = await datasetService.getWorkspace({
          page,
          page_size: ELIGIBLE_PAGE_SIZE,
        });
        allItems = allItems.concat(normalizeItems(response));
      }

      const datasetResponse = await datasetService.getDatasetEmails(
        datasetId,
        { page: 1, page_size: 1 }
      );

      const datasetTotal = getPagination(
        datasetResponse,
        normalizeItems(datasetResponse).length,
        1,
        1
      ).total;

      const existingIds = new Set();
      const datasetPageSize = 100;

      for (
        let page = 1;
        page <= Math.ceil(datasetTotal / datasetPageSize);
        page += 1
      ) {
        const response = await datasetService.getDatasetEmails(
          datasetId,
          { page, page_size: datasetPageSize }
        );

        for (const item of normalizeItems(response)) {
          existingIds.add(item.email_id);
        }
      }

      const available = allItems.filter(
        (item) => item.email_id && !existingIds.has(item.email_id)
      );

      setEligibleEmails(available);
      setEligibleTotal(available.length);
      setEligibleTotalPages(
        Math.ceil(available.length / ELIGIBLE_PAGE_SIZE)
      );
      setEligiblePage(1);
      setSelectedEligibleIds([]);
    } catch (err) {
      setEligibleError(
        getErrorMessage(err, "Failed to load eligible emails.")
      );
      setEligibleEmails([]);
      setEligibleTotal(0);
      setEligibleTotalPages(0);
    } finally {
      setEligibleLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    if (!addOpen || !datasetId) return;
    loadEligibleEmails();
  }, [addOpen, datasetId, loadEligibleEmails]);

  const filteredEligibleEmails = useMemo(() => {
    const query = eligibleSearch.trim().toLowerCase();
    if (!query) return eligibleEmails;

    return eligibleEmails.filter((email) =>
      [
        email.subject,
        email.sender,
        email.ground_truth,
        email.source,
        email.email_id,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query))
    );
  }, [eligibleEmails, eligibleSearch]);

  const eligiblePageItems = useMemo(() => {
    const start = (eligiblePage - 1) * ELIGIBLE_PAGE_SIZE;
    return filteredEligibleEmails.slice(
      start,
      start + ELIGIBLE_PAGE_SIZE
    );
  }, [filteredEligibleEmails, eligiblePage]);

  const visibleEligibleIds = eligiblePageItems.map(
    (item) => item.email_id
  );

  const allVisibleEligibleSelected =
    visibleEligibleIds.length > 0 &&
    visibleEligibleIds.every((id) =>
      selectedEligibleIds.includes(id)
    );

  const toggleEligible = (emailId) => {
    setSelectedEligibleIds((previous) =>
      previous.includes(emailId)
        ? previous.filter((id) => id !== emailId)
        : [...previous, emailId]
    );
  };

  const toggleAllEligible = () => {
    setSelectedEligibleIds((previous) => {
      if (allVisibleEligibleSelected) {
        return previous.filter(
          (id) => !visibleEligibleIds.includes(id)
        );
      }

      return [
        ...new Set([...previous, ...visibleEligibleIds]),
      ];
    });
  };

  const toggleDatasetEmail = (emailId) => {
    setSelectedEmailIds((previous) =>
      previous.includes(emailId)
        ? previous.filter((id) => id !== emailId)
        : [...previous, emailId]
    );
  };

  const toggleAllDatasetEmails = () => {
    const visibleIds = emails.map((item) => item.email_id);
    const allSelected =
      visibleIds.length > 0 &&
      visibleIds.every((id) => selectedEmailIds.includes(id));

    setSelectedEmailIds((previous) =>
      allSelected
        ? previous.filter((id) => !visibleIds.includes(id))
        : [...new Set([...previous, ...visibleIds])]
    );
  };

  const handleAddEmails = async () => {
    if (!datasetId || selectedEligibleIds.length === 0) return;

    setAddLoading(true);
    setOperationError("");
    setOperationMessage("");

    try {
      const response = await datasetService.addDatasetEmails(
        datasetId,
        selectedEligibleIds
      );

      setOperationMessage(
        response?.message || `Added ${selectedEligibleIds.length} email(s).`
      );
      setAddOpen(false);
      setSelectedEligibleIds([]);
      await loadDatasetEmails();
      onDatasetUpdated?.();
    } catch (err) {
      setOperationError(
        getErrorMessage(err, "Failed to add selected emails.")
      );
    } finally {
      setAddLoading(false);
    }
  };

  const handleRemoveEmails = async () => {
    if (!datasetId || selectedEmailIds.length === 0) return;

    const confirmed = window.confirm(
      `Remove ${selectedEmailIds.length} selected email(s) from this dataset? ` +
        "The original emails and existing dataset versions will not be deleted."
    );

    if (!confirmed) return;

    setRemoveLoading(true);
    setOperationError("");
    setOperationMessage("");

    try {
      const response = await datasetService.removeDatasetEmails(
        datasetId,
        selectedEmailIds
      );

      setOperationMessage(
        response?.message ||
          `Removed ${selectedEmailIds.length} email(s) from the dataset.`
      );
      setSelectedEmailIds([]);
      await loadDatasetEmails();
      onDatasetUpdated?.();
    } catch (err) {
      setOperationError(
        getErrorMessage(err, "Failed to remove selected emails.")
      );
    } finally {
      setRemoveLoading(false);
    }
  };

  const handleEditDataset = async (event) => {
    event.preventDefault();
    if (!datasetId) return;

    const name = editName.trim();
    if (!name) {
      setOperationError("Dataset name cannot be empty.");
      return;
    }

    setEditLoading(true);
    setOperationError("");
    setOperationMessage("");

    try {
      await datasetService.updateDataset(datasetId, {
        name,
        description: editDescription.trim() || null,
      });

      setOperationMessage("Dataset information updated successfully.");
      setEditOpen(false);
      onDatasetUpdated?.();
    } catch (err) {
      setOperationError(
        getErrorMessage(err, "Failed to update dataset.")
      );
    } finally {
      setEditLoading(false);
    }
  };

  const closeAddModal = () => {
    setAddOpen(false);
    setEligibleSearch("");
    setEligiblePage(1);
    setSelectedEligibleIds([]);
    setEligibleError("");
  };

  if (!open) return null;

  return (
    <>
      <div
        className="dataset-drawer-backdrop"
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            onClose?.();
          }
        }}
      >
        <aside
          className="dataset-details-drawer dataset-info-drawer"
          role="dialog"
          aria-modal="true"
          aria-labelledby="dataset-info-title"
        >
          <header className="dataset-details-drawer__header">
            <div className="dataset-info-drawer__heading">
              <span className="dataset-details-drawer__eyebrow">
                Dataset Management
              </span>
              <h2 id="dataset-info-title">Dataset Details</h2>
              {dataset && (
                <span className="dataset-info-drawer__name">
                  {dataset.name || "Untitled Dataset"}
                </span>
              )}
            </div>

            <button
              type="button"
              className="dataset-icon-button"
              onClick={onClose}
              aria-label="Close dataset details"
            >
              <X size={20} />
            </button>
          </header>

          {loading ? (
            <LoadingState message="Loading dataset details..." />
          ) : error ? (
            <div
              className="dataset-details-drawer__state dataset-details-drawer__state--error"
              role="alert"
            >
              <AlertTriangle size={24} />
              <p>{error}</p>
            </div>
          ) : !dataset ? (
            <div className="dataset-details-drawer__state">
              <Database size={28} />
              <p>No dataset selected.</p>
            </div>
          ) : (
            <div className="dataset-details-drawer__body">
              {operationError && (
                <div className="dataset-inline-alert dataset-inline-alert--error" role="alert">
                  <AlertTriangle size={17} />
                  <span>{operationError}</span>
                  <button
                    type="button"
                    className="dataset-icon-button"
                    onClick={() => setOperationError("")}
                    aria-label="Dismiss error"
                  >
                    <X size={15} />
                  </button>
                </div>
              )}

              {operationMessage && (
                <div className="dataset-inline-alert dataset-inline-alert--success" role="status">
                  <Check size={17} />
                  <span>{operationMessage}</span>
                  <button
                    type="button"
                    className="dataset-icon-button"
                    onClick={() => setOperationMessage("")}
                    aria-label="Dismiss message"
                  >
                    <X size={15} />
                  </button>
                </div>
              )}

              <section className="dataset-details-card">
                <div className="dataset-details-card__title">
                  <Database size={17} />
                  <h3>Dataset Information</h3>
                  <button
                    type="button"
                    className="dataset-button dataset-button--secondary"
                    onClick={() => {
                      setEditName(dataset.name ?? "");
                      setEditDescription(dataset.description ?? "");
                      setEditOpen(true);
                    }}
                  >
                    <Pencil size={15} />
                    Edit
                  </button>
                </div>

                <DetailField label="Dataset Name" value={dataset.name} />
                <DetailField label="Dataset ID" value={dataset.id} code />
                <DetailField label="Description" value={dataset.description} />

                <div className="dataset-details-field">
                  <span>Status</span>
                  <strong>
                    <span
                      className={`dataset-label ${getStatusClass(dataset.status)}`}
                    >
                      {String(dataset.status ?? "unknown").replaceAll("_", " ")}
                    </span>
                  </strong>
                </div>

                <DetailField
                  label="Created At"
                  value={formatDate(dataset.created_at)}
                />
                <DetailField
                  label="Updated At"
                  value={formatDate(dataset.updated_at)}
                />
              </section>

              <section className="dataset-details-card">
                <div className="dataset-details-card__title">
                  <Mail size={17} />
                  <h3>Sample Statistics</h3>
                </div>
                <DetailField label="Total Samples" value={dataset.sample_count} />
                <DetailField label="Normal Emails" value={dataset.normal_count} />
                <DetailField label="Bombing Emails" value={dataset.bombing_count} />
              </section>

              <section className="dataset-details-card">
                <div className="dataset-details-card__title">
                  <Layers size={17} />
                  <h3>Version Information</h3>
                </div>
                <DetailField label="Version Count" value={dataset.version_count} />
                <p className="dataset-help-text">
                  Existing version snapshots remain unchanged when dataset
                  memberships are added or removed.
                </p>
              </section>

              <section className="dataset-details-card">
                <div className="dataset-details-card__title">
                  <ShieldCheck size={17} />
                  <h3>Feature Schema</h3>
                </div>
                {dataset.feature_schema &&
                typeof dataset.feature_schema === "object" ? (
                  Object.entries(dataset.feature_schema).map(([key, value]) => (
                    <DetailField
                      key={key}
                      label={key}
                      value={value}
                      code
                    />
                  ))
                ) : (
                  <DetailField
                    label="Schema"
                    value={dataset.feature_schema}
                    code
                  />
                )}
              </section>

              <section className="dataset-details-card dataset-email-card">
                <div className="dataset-details-card__title">
                  <Mail size={17} />
                  <h3>Dataset Emails</h3>
                  <span className="dataset-count-badge">
                    {emailPagination.total}
                  </span>
                  <div className="dataset-email-card__actions">
                    <button
                      type="button"
                      className="dataset-button dataset-button--secondary"
                      onClick={() => setAddOpen(true)}
                    >
                      <Plus size={15} />
                      Add Emails
                    </button>
                    <button
                      type="button"
                      className="dataset-button dataset-button--danger"
                      onClick={handleRemoveEmails}
                      disabled={selectedEmailIds.length === 0 || removeLoading}
                    >
                      {removeLoading ? (
                        <LoaderCircle size={15} className="dataset-spinner" />
                      ) : (
                        <Trash2 size={15} />
                      )}
                      Remove ({selectedEmailIds.length})
                    </button>
                  </div>
                </div>

                <div className="dataset-email-toolbar">
                  <label className="dataset-search">
                    <Search size={16} />
                    <input
                      type="search"
                      value={emailSearch}
                      placeholder="Search subject, sender..."
                      onChange={(event) => {
                        setEmailSearch(event.target.value);
                        setEmailPage(1);
                      }}
                    />
                  </label>
                  <button
                    type="button"
                    className="dataset-icon-button"
                    onClick={loadDatasetEmails}
                    disabled={emailLoading}
                    aria-label="Refresh dataset emails"
                  >
                    <RefreshCw size={16} />
                  </button>
                </div>

                {emailError && (
                  <div className="dataset-inline-alert dataset-inline-alert--error" role="alert">
                    <AlertTriangle size={16} />
                    {emailError}
                  </div>
                )}

                {emailLoading ? (
                  <LoadingState message="Loading dataset emails..." />
                ) : emails.length === 0 ? (
                  <div className="dataset-empty-state">
                    <Inbox size={26} />
                    <p>No dataset emails found.</p>
                  </div>
                ) : (
                  <div className="dataset-table-wrap">
                    <table className="dataset-table">
                      <thead>
                        <tr>
                          <th>
                            <input
                              type="checkbox"
                              checked={allVisibleEligibleSelected && false}
                              onChange={toggleAllDatasetEmails}
                              aria-label="Select all emails on this page"
                            />
                          </th>
                          <th>Subject</th>
                          <th>Sender</th>
                          <th>Ground Truth</th>
                        </tr>
                      </thead>
                      <tbody>
                        {emails.map((email) => (
                          <tr key={email.email_id}>
                            <td>
                              <input
                                type="checkbox"
                                checked={selectedEmailIds.includes(email.email_id)}
                                onChange={() => toggleDatasetEmail(email.email_id)}
                                aria-label={`Select ${email.subject || email.email_id}`}
                              />
                            </td>
                            <td title={email.subject || ""}>
                              {email.subject || "—"}
                            </td>
                            <td title={email.sender || ""}>
                              {email.sender || "—"}
                            </td>
                            <td>
                              <span
                                className={`dataset-label dataset-label--${String(
                                  email.ground_truth || "unknown"
                                ).toLowerCase()}`}
                              >
                                {email.ground_truth || "unknown"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="dataset-pagination">
                  <span>
                    {Math.min((emailPagination.page - 1) * emailPagination.pageSize + 1, emailPagination.total)} - {Math.min(emailPagination.page * emailPagination.pageSize, emailPagination.total)} / Total {emailPagination.total}
                  </span>
                  <div>
                    <button
                      type="button"
                      className="dataset-icon-button"
                      disabled={emailPage <= 1 || emailLoading}
                      onClick={() => setEmailPage((page) => Math.max(1, page - 1))}
                      aria-label="Previous page"
                      title="Previous page"
                    >
                      <ChevronLeft size={16} aria-hidden="true" />
                      <span>Previous</span>
                    </button>
                    <span className="dataset-table-pagination__page">
                      Page {emailPagination.page} of {emailPagination.totalPages}
                    </span>
                    <button
                      type="button"
                      className="dataset-icon-button"
                      disabled={
                        emailPage >= emailPagination.totalPages || emailLoading
                      }
                      onClick={() => setEmailPage((page) => page + 1)}
                      aria-label="Next page"
                      title="Next page"
                    >
                      <span>Next</span>
                      <ChevronRight size={16} aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </section>

              <section className="dataset-details-card">
                <div className="dataset-details-card__title">
                  <FileText size={17} />
                  <h3>Record</h3>
                </div>
                <DetailField label="Dataset ID" value={dataset.id} code />
                <DetailField label="Created" value={formatDate(dataset.created_at)} />
                <DetailField
                  label="Last Updated"
                  value={formatDate(dataset.updated_at)}
                />
              </section>
            </div>
          )}
        </aside>
      </div>

      {addOpen && (
        <Modal title="Add Emails to Dataset" onClose={closeAddModal} wide>
          <p className="dataset-help-text">
            Select eligible feature-extracted emails that are not already
            members of this dataset.
          </p>

          {eligibleError && (
            <div className="dataset-inline-alert dataset-inline-alert--error" role="alert">
              <AlertTriangle size={16} />
              {eligibleError}
              <button
                type="button"
                className="dataset-icon-button"
                onClick={loadEligibleEmails}
                aria-label="Retry loading eligible emails"
              >
                <RefreshCw size={15} />
              </button>
            </div>
          )}

          <div className="dataset-email-toolbar">
            <label className="dataset-search">
              <Search size={16} />
              <input
                type="search"
                value={eligibleSearch}
                placeholder="Search eligible emails..."
                onChange={(event) => {
                  setEligibleSearch(event.target.value);
                  setEligiblePage(1);
                }}
              />
            </label>
            <button
              type="button"
              className="dataset-icon-button"
              onClick={loadEligibleEmails}
              disabled={eligibleLoading}
              aria-label="Refresh eligible emails"
            >
              <RefreshCw size={16} />
            </button>
          </div>

          <div className="dataset-selection-summary">
            <span>{eligibleTotal} available emails</span>
            <span>{selectedEligibleIds.length} selected</span>
          </div>

          {eligibleLoading ? (
            <LoadingState message="Loading eligible emails..." />
          ) : eligiblePageItems.length === 0 ? (
            <div className="dataset-empty-state">
              <Inbox size={26} />
              <p>No eligible emails available.</p>
            </div>
          ) : (
            <div className="dataset-table-wrap dataset-table-wrap--modal">
              <table className="dataset-table">
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        checked={allVisibleEligibleSelected}
                        onChange={toggleAllEligible}
                        aria-label="Select all visible eligible emails"
                      />
                    </th>
                    <th>Subject</th>
                    <th>Sender</th>
                    <th>Ground Truth</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {eligiblePageItems.map((email) => (
                    <tr key={email.email_id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedEligibleIds.includes(email.email_id)}
                          onChange={() => toggleEligible(email.email_id)}
                          aria-label={`Select ${email.subject || email.email_id}`}
                        />
                      </td>
                      <td title={email.subject || ""}>
                        {email.subject || "—"}
                      </td>
                      <td title={email.sender || ""}>
                        {email.sender || "—"}
                      </td>
                      <td>{email.ground_truth || "—"}</td>
                      <td>{email.source || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="dataset-pagination">
            <span>
              {filteredEligibleEmails.length > 0
                ? `${(eligiblePage - 1) * ELIGIBLE_PAGE_SIZE + 1} - ${Math.min(eligiblePage * ELIGIBLE_PAGE_SIZE, filteredEligibleEmails.length)} / Total ${filteredEligibleEmails.length}`
                : "0 - 0 / Total 0"}
            </span>
            <div>
              <button
                type="button"
                className="dataset-icon-button"
                disabled={eligiblePage <= 1}
                onClick={() => setEligiblePage((page) => Math.max(1, page - 1))}
                aria-label="Previous eligible page"
                title="Previous page"
              >
                <ChevronLeft size={16} aria-hidden="true" />
                <span>Previous</span>
              </button>
              <span className="dataset-table-pagination__page">
                Page {eligiblePage} of {Math.max(1, Math.ceil(filteredEligibleEmails.length / ELIGIBLE_PAGE_SIZE))}
              </span>
              <button
                type="button"
                className="dataset-icon-button"
                disabled={
                  eligiblePage >=
                  Math.ceil(filteredEligibleEmails.length / ELIGIBLE_PAGE_SIZE)
                }
                onClick={() => setEligiblePage((page) => page + 1)}
                aria-label="Next eligible page"
                title="Next page"
              >
                <span>Next</span>
                <ChevronRight size={16} aria-hidden="true" />
              </button>
            </div>
          </div>

          <footer className="dataset-modal__footer">
            <button
              type="button"
              className="dataset-button dataset-button--secondary"
              onClick={closeAddModal}
            >
              Cancel
            </button>
            <button
              type="button"
              className="dataset-button dataset-button--primary"
              onClick={handleAddEmails}
              disabled={selectedEligibleIds.length === 0 || addLoading}
            >
              {addLoading ? (
                <LoaderCircle size={16} className="dataset-spinner" />
              ) : (
                <Plus size={16} />
              )}
              Add Selected ({selectedEligibleIds.length})
            </button>
          </footer>
        </Modal>
      )}

      {editOpen && (
        <Modal
          title="Edit Dataset"
          onClose={() => setEditOpen(false)}
        >
          <form className="dataset-form" onSubmit={handleEditDataset}>
            <label>
              Dataset Name
              <input
                type="text"
                value={editName}
                onChange={(event) => setEditName(event.target.value)}
                maxLength={255}
                required
              />
            </label>

            <label>
              Description
              <textarea
                value={editDescription}
                onChange={(event) => setEditDescription(event.target.value)}
                rows={4}
              />
            </label>

            <p className="dataset-help-text">
              Editing changes only the dataset name and description. It does
              not modify emails, labels, features, or existing versions.
            </p>

            <footer className="dataset-modal__footer">
              <button
                type="button"
                className="dataset-button dataset-button--secondary"
                onClick={() => setEditOpen(false)}
                disabled={editLoading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="dataset-button dataset-button--primary"
                disabled={editLoading || !editName.trim()}
              >
                {editLoading ? (
                  <LoaderCircle size={16} className="dataset-spinner" />
                ) : (
                  <Check size={16} />
                )}
                Save Changes
              </button>
            </footer>
          </form>
        </Modal>
      )}
    </>
  );
}
