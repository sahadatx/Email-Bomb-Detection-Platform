import React from "react";
import {
  CalendarDays,
  Cpu,
  FileText,
  Hash,
  Play,
  History,
  Pencil,
  Power,
  X,
} from "lucide-react";

import ModelStatusBadge from "./ModelStatusBadge";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function ModelDetails({
  model,
  open,
  onClose,
  onEdit,
  onToggleStatus,
  onStartTraining,
  onViewTrainingHistory,
  onDelete,
  canDelete = false,
}) {
  if (!open || !model) return null;

  const isActive = model.status === "active";

  return (
    <div
      className="ml-drawer-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose?.();
        }
      }}
    >
      <aside
        className="ml-drawer ml-drawer--details"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ml-model-details-title"
      >
        <header className="ml-drawer__header">
          <div>
            <span className="ml-eyebrow">
              MODEL DETAILS
            </span>

            <h2 id="ml-model-details-title">
              {model.name || "Unnamed model"}
            </h2>

            <p>Model definition and configuration</p>
          </div>

          <button
            type="button"
            className="ml-icon-button"
            aria-label="Close details"
            onClick={onClose}
          >
            <X size={19} />
          </button>
        </header>

        <div className="ml-drawer__body">
          <div className="ml-details-hero">
            <div className="ml-details-hero__icon">
              <Cpu size={25} />
            </div>

            <div className="ml-details-hero__content">
              <strong>{model.name || "Unnamed model"}</strong>
              <span>{model.algorithm || "Algorithm not specified"}</span>
            </div>

            <ModelStatusBadge status={model.status} />
          </div>

          <div className="ml-details-grid">
            <div className="ml-detail-item">
              <span className="ml-detail-item__label">
                <Hash size={14} /> Model ID
              </span>
              <code>{model.id || "—"}</code>
            </div>

            <div className="ml-detail-item">
              <span className="ml-detail-item__label">
                <Cpu size={14} /> Algorithm
              </span>
              <strong>{model.algorithm || "—"}</strong>
            </div>

            <div className="ml-detail-item">
              <span className="ml-detail-item__label">
                <Cpu size={14} /> Model type
              </span>
              <strong>{model.model_type || "classifier"}</strong>
            </div>

            <div className="ml-detail-item">
              <span className="ml-detail-item__label">
                <CalendarDays size={14} /> Created at
              </span>
              <strong>{formatDate(model.created_at)}</strong>
            </div>

            <div className="ml-detail-item">
              <span className="ml-detail-item__label">
                <CalendarDays size={14} /> Updated at
              </span>
              <strong>{formatDate(model.updated_at)}</strong>
            </div>
          </div>

          <section className="ml-details-section">
            <h3>Model activity</h3>
            <p className="ml-details-description">Training runs: {model.training_run_count ?? "—"}</p>
            <p className="ml-details-description">Latest run: {model.latest_training_run?.id || "—"} {model.latest_training_run?.status ? `· ${model.latest_training_run.status}` : ""}</p>
            <p className="ml-details-description">Registered versions: {model.version_count ?? "—"} · Latest version: {model.latest_version ?? "—"}</p>
            {model.created_by && <p className="ml-details-description">Created by: {model.created_by}</p>}
          </section>

          <section className="ml-details-section">
            <h3>
              <FileText size={16} />
              Description
            </h3>

            <p className="ml-details-description">
              {model.description || "No description provided."}
            </p>
          </section>

          <section className="ml-details-section">
            <h3>Hyperparameters</h3>

            <pre className="ml-json-view">
              {JSON.stringify(
                model.hyperparameters || {},
                null,
                2
              )}
            </pre>
          </section>

          {onStartTraining && <section className="ml-details-section">
            <h3>Training</h3>
            <p className="ml-details-description">
              Start a new training run using this model or
              inspect its training history.
            </p>

            <div className="ml-details-actions">
              <button
                type="button"
                className="ml-button ml-button--primary"
                disabled={!isActive}
                title={
                  isActive
                    ? "Start training with this model"
                    : "Activate the model before starting training"
                }
                onClick={() => onStartTraining?.(model)}
              >
                <Play size={16} />
                Start Training
              </button>

              <button
                type="button"
                className="ml-button ml-button--secondary"
                onClick={() =>
                  onViewTrainingHistory?.(model)
                }
              >
                <History size={16} />
                Training History
              </button>
            </div>
          </section>}
        </div>

        <footer className="ml-drawer__footer">
          <button
            type="button"
            className="ml-button ml-button--secondary"
            onClick={onClose}
          >
            Close
          </button>

          {onToggleStatus && <button
            type="button"
            className="ml-button ml-button--secondary"
            onClick={() => onToggleStatus?.(model)}
          >
            <Power size={16} />
            {isActive ? "Deactivate" : "Activate"}
          </button>}

          {onEdit && <button
            type="button"
            className="ml-button ml-button--primary"
            onClick={() => onEdit?.(model)}
          >
            <Pencil size={16} />
            Edit model
          </button>}
          {canDelete && <button type="button" className="ml-button ml-button--danger" onClick={() => onDelete?.(model)}>Delete</button>}
        </footer>
      </aside>
    </div>
  );
}
