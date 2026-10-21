
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../../../core/auth/AuthProvider";
import {
  AlertCircle,
  Cpu,
  Plus,
  RefreshCw,
  ShieldCheck,
  Users,
  Search,
  Layers,
  X,
} from "lucide-react";

import { modelService } from "../services/modelService";
import { ML_ALGORITHM_LABELS } from "../types";
import ModelTable from "../components/ModelTable";
import ModelForm from "../components/ModelForm";
import ModelDetails from "../components/ModelDetails";
import ModelPagination from "../components/ModelPagination";
import { getVersions } from "../services/modelRegistryService";
import "../styles/ml-models.css";

const PAGE_SIZE = 30;

function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail;
  return (
    (typeof detail === "string" ? detail : detail?.message) ||
    error?.response?.data?.message ||
    error?.message ||
    fallback
  );
}

function normalizeModels(response) {
  if (Array.isArray(response)) return response;
  if (Array.isArray(response?.items)) return response.items;
  return [];
}

function getTrainingCount(model) {
  return (
    model.training_run_count ??
    model.training_runs_count ??
    model.training_runs?.length ??
    0
  );
}

function getVersionCount(model) {
  return (
    model.version_count ??
    model.versions_count ??
    model.versions?.length ??
    0
  );
}

export default function ModelsPage() {
  const { user } = useAuth();
  const canManageModels = ["ADMIN", "SECURITY_ANALYST"].includes(user?.role);
  const [routeParams] = useSearchParams();
  const [models, setModels] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [algorithmFilter, setAlgorithmFilter] = useState("all");

  const [formOpen, setFormOpen] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const [selectedModel, setSelectedModel] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [statusUpdatingId, setStatusUpdatingId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [algorithmOptions, setAlgorithmOptions] = useState([]);
  const [toast, setToast] = useState("");
  const [deleteAllowed, setDeleteAllowed] = useState(false);
  const updateSearch = (value) => { setPage(1); setSearch(value); };

  const loadModels = useCallback(async () => {
    setLoading(true);
    setPageError("");

    try {
      const [modelsResponse, countResponse, summaryResponse, algorithmsResponse] = await Promise.all([
        modelService.getModels({ offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, search: search.trim() || undefined, status: statusFilter === "all" ? undefined : statusFilter, algorithm: algorithmFilter === "all" ? undefined : algorithmFilter }),
        modelService.getModelCount({ search: search.trim() || undefined, status: statusFilter === "all" ? undefined : statusFilter, algorithm: algorithmFilter === "all" ? undefined : algorithmFilter }),
        modelService.getSummary(), modelService.getAlgorithms(),
      ]);

      const modelList = normalizeModels(modelsResponse);
      const summaries = Object.fromEntries((summaryResponse.items || []).map((item) => [item.model_definition_id, item]));
      setModels(modelList.map((model) => ({ ...model, ...(summaries[model.id] || {}) })));
      setSummary(summaryResponse);
      setAlgorithmOptions(algorithmsResponse);
      setTotal(countResponse.total ?? modelList.length);

      setSelectedModel((current) =>
        current
          ? modelList.find((model) => model.id === current.id) || current
          : null
      );
    } catch (error) {
      setPageError(getErrorMessage(error, "Failed to load models."));
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, algorithmFilter, page]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const modelTypes = useMemo(() => {
    return [...new Set(
      models
        .map((model) => model.model_type || model.type)
        .filter(Boolean)
    )].sort();
  }, [models]);

  const algorithms = useMemo(() => {
    const known = algorithmOptions.map((item) => item.algorithm);
    const fromModels = models.map((model) => model.algorithm).filter(Boolean);

    return [...new Set([...known, ...fromModels])].sort();
  }, [models, algorithmOptions]);

  const filteredModels = useMemo(() => {
      return models.filter((model) => {
      const type = String(model.model_type || model.type || "").toLowerCase();
      const matchesType =
        typeFilter === "all" || type === typeFilter.toLowerCase();
      return matchesType;
    });
  }, [models, typeFilter]);

  const activeCount = summary?.active_models ?? models.filter((model) => model.status === "active").length;

  const inactiveCount = summary?.inactive_models ?? models.filter((model) => model.status === "inactive").length;

  const trainedVersionCount = summary?.trained_versions ?? models.reduce((sum, model) => sum + getVersionCount(model), 0);

  const openCreateForm = () => {
    setEditingModel(null);
    setFormError("");
    setDetailsOpen(false);
    setFormOpen(true);
  };

  const openEditForm = (model) => {
    setDetailsOpen(false);
    setEditingModel(model);
    setFormError("");
    setFormOpen(true);
  };

  const openDetails = (model) => {
    setSelectedModel(model);
    setDetailsOpen(true);
    setDeleteAllowed(false);
    Promise.all([
      modelService.getTrainingHistory(model.id, { offset: 0, limit: 1 }),
      getVersions({ model_definition_id: model.id, offset: 0, limit: 1 }),
    ]).then(([runs, versions]) => setDeleteAllowed((runs.total || 0) === 0 && (versions.total || 0) === 0)).catch(() => setDeleteAllowed(false));
  };

  useEffect(() => {
    const modelId = routeParams.get("model_id");
    if (modelId) modelService.getModelById(modelId).then(openDetails).catch((error) => setPageError(getErrorMessage(error, "Unable to load model details.")));
  }, []);

  const closeForm = () => {
    if (formSubmitting) return;

    setFormOpen(false);
    setEditingModel(null);
    setFormError("");
  };

  const handleSubmit = async (payload) => {
    setFormSubmitting(true);
    setFormError("");

    try {
      if (editingModel) {
        const updatePayload = { name: payload.name, description: payload.description, algorithm: payload.algorithm, hyperparameters: payload.hyperparameters };

        await modelService.updateModel(editingModel.id, updatePayload);
      } else {
        await modelService.createModel(payload);
      }

      setFormOpen(false);
      setEditingModel(null);
      await loadModels();
      setToast(editingModel ? "Model updated." : "Model created.");
    } catch (error) {
      setFormError(getErrorMessage(error, "Unable to save the model."));
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleToggleStatus = async (model) => {
    const nextStatus =
      model.status === "active" ? "inactive" : "active";

    const action = nextStatus === "active" ? "activate" : "deactivate";

    if (!window.confirm(`Are you sure you want to ${action} "${model.name}"?`)) {
      return;
    }

    setStatusUpdatingId(model.id);
    setPageError("");

    try {
      await modelService.updateModelStatus(model.id, nextStatus);
      await loadModels();
    } catch (error) {
      setPageError(
        getErrorMessage(error, `Unable to ${action} the model.`)
      );
    } finally {
      setStatusUpdatingId(null);
    }
  };

  const handleDeleteModel = async (model) => {
    if (!window.confirm(`Delete model “${model.name}”? This cannot be undone.`)) return;
    setPageError("");
    try {
      await modelService.deleteModel(model.id);
      setDetailsOpen(false); setSelectedModel(null); await loadModels(); setToast("Model deleted.");
    } catch (error) { setPageError(getErrorMessage(error, "Unable to delete model.")); }
  };

  const startTraining = (model) => {
    setDetailsOpen(false);
    window.location.assign(`/ml-models/training-runs?model_definition_id=${encodeURIComponent(model.id)}&create=1`);
  };

  const viewTrainingHistory = (model) => {
    setDetailsOpen(false);
    window.location.assign(`/ml-models/training-runs?model_definition_id=${encodeURIComponent(model.id)}`);
  };

  const resetFilters = () => {
    setPage(1);
    setSearch("");
    setStatusFilter("all");
    setTypeFilter("all");
    setAlgorithmFilter("all");
  };

  const hasActiveFilters =
    search.trim() !== "" ||
    statusFilter !== "all" ||
    typeFilter !== "all" ||
    algorithmFilter !== "all";

  return (
    <main className="ml-page ml-models-page">
      <div className="ml-page__container">
        <header className="ml-page-header">
          <div className="ml-page-header__content">
            <div className="ml-breadcrumb">
              <span>Machine Learning</span>
              <span className="ml-breadcrumb__separator">/</span>
              <strong>Models</strong>
            </div>

            <div className="ml-page-title-row">
              <div className="ml-page-title-icon">
                <Cpu size={25} />
              </div>
              <div>
                <h1>Models</h1>
                <p>
                  Create, configure, and manage machine learning models.
                </p>
              </div>
            </div>
          </div>

          <div className="ml-page-header__actions">
            <button
              type="button"
              className="ml-button ml-button--secondary"
              onClick={loadModels}
              disabled={loading}
            >
              <RefreshCw
                size={16}
                className={loading ? "ml-spin" : ""}
              />
              Refresh
            </button>

            {canManageModels && <button
              type="button"
              className="ml-button ml-button--primary"
              onClick={openCreateForm}
            >
              <Plus size={17} />
              Create model
            </button>}
          </div>
        </header>

        {pageError && (
          <div className="ml-alert ml-alert--error" role="alert">
            <AlertCircle size={17} />
            <span>{pageError}</span>
            <button
              type="button"
              className="ml-alert__action"
              onClick={() => setPageError("")}
            >
              Dismiss
            </button>
          </div>
        )}

        <section
          className="ml-stats-grid"
          aria-label="Model statistics"
        >
          <article className="ml-stat-card">
            <div className="ml-stat-card__top">
              <span>Total models</span>
              <span className="ml-stat-card__icon ml-stat-card__icon--blue">
                <Cpu size={19} />
              </span>
            </div>
            <strong>{loading ? "—" : summary?.total_models ?? total}</strong>
            <span className="ml-stat-card__footnote">
              Registered model definitions
            </span>
          </article>

          <article className="ml-stat-card">
            <div className="ml-stat-card__top">
              <span>Active models</span>
              <span className="ml-stat-card__icon ml-stat-card__icon--green">
                <ShieldCheck size={19} />
              </span>
            </div>
            <strong>{loading ? "—" : activeCount}</strong>
            <span className="ml-stat-card__footnote">
              Currently active
            </span>
          </article>

          <article className="ml-stat-card">
            <div className="ml-stat-card__top">
              <span>Inactive models</span>
              <span className="ml-stat-card__icon ml-stat-card__icon--gray">
                <Users size={19} />
              </span>
            </div>
            <strong>{loading ? "—" : inactiveCount}</strong>
            <span className="ml-stat-card__footnote">
              Not currently active
            </span>
          </article>

          <article className="ml-stat-card">
            <div className="ml-stat-card__top">
              <span>Trained versions</span>
              <span className="ml-stat-card__icon ml-stat-card__icon--purple">
                <Layers size={19} />
              </span>
            </div>
            <strong>{loading ? "—" : trainedVersionCount}</strong>
            <span className="ml-stat-card__footnote">
              Registered model versions
            </span>
          </article>
        </section>

        <section className="ml-panel">
          <div className="ml-panel__header">
            <div>
              <h2>Model definitions</h2>
              <p>Manage your registered machine learning models.</p>
            </div>
            <span className="ml-count-badge">
              {loading ? "—" : filteredModels.length} shown
            </span>
          </div>

          <div className="ml-filters">
            <div className="ml-search-field">
              <Search size={17} />
              <input
                type="search"
                value={search}
                onChange={(event) => updateSearch(event.target.value)}
                placeholder="Search name or description..."
                aria-label="Search models"
              />
              {search && (
                <button
                  type="button"
                  className="ml-icon-button"
                  aria-label="Clear search"
                  onClick={() => updateSearch("")}
                >
                  <X size={15} />
                </button>
              )}
            </div>

            <select
              className="ml-filter-select"
              value={statusFilter}
              onChange={(event) => { setPage(1); setStatusFilter(event.target.value); }}
              aria-label="Filter by status"
            >
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>

            <select
              className="ml-filter-select"
              value={typeFilter}
              onChange={(event) => { setPage(1); setTypeFilter(event.target.value); }}
              aria-label="Filter by type"
            >
              <option value="all">All types</option>
              {modelTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>

            <select
              className="ml-filter-select"
              value={algorithmFilter}
              onChange={(event) => { setPage(1); setAlgorithmFilter(event.target.value); }}
              aria-label="Filter by algorithm"
            >
              <option value="all">All algorithms</option>
              {algorithms.map((algorithm) => (
                <option key={algorithm} value={algorithm}>
                  {ML_ALGORITHM_LABELS?.[algorithm] || algorithm}
                </option>
              ))}
            </select>

          </div>

          <div className="ml-models-filter-reset">
            <button
              type="button"
              className="ml-button ml-button--secondary"
              onClick={resetFilters}
              disabled={!hasActiveFilters}
            >
              <X size={15} />
              Reset Filters
            </button>
          </div>

          <ModelTable
            models={filteredModels}
            loading={loading}
            error=""
            onView={openDetails}
            onEdit={canManageModels ? openEditForm : undefined}
            onToggleStatus={canManageModels ? handleToggleStatus : undefined}
            statusUpdatingId={statusUpdatingId}
          />

          {!loading && hasActiveFilters && filteredModels.length === 0 && (
            <div className="ml-table-feedback">
              No models match your filters.
            </div>
          )}

          <ModelPagination page={page} pageSize={PAGE_SIZE} total={total} loading={loading} onPage={setPage} />

          {statusUpdatingId && (
            <div className="ml-table-feedback" role="status">
              Updating model status...
            </div>
          )}
        </section>
      </div>

      <ModelForm
        open={formOpen}
        model={editingModel}
        algorithms={algorithmOptions}
        submitting={formSubmitting}
        error={formError}
        onClose={closeForm}
        onSubmit={handleSubmit}
      />

      <ModelDetails
        model={selectedModel}
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        onEdit={canManageModels ? openEditForm : undefined}
        onToggleStatus={canManageModels ? handleToggleStatus : undefined}
        onStartTraining={canManageModels ? startTraining : undefined}
        onViewTrainingHistory={viewTrainingHistory}
        onDelete={handleDeleteModel}
        canDelete={canManageModels && deleteAllowed}
      />
      {toast && <div className="ml-toast" role="status" onAnimationEnd={() => setToast("")}>{toast}</div>}
    </main>
  );
}
