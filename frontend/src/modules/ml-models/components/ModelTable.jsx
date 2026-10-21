import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  Eye,
  Pencil,
  Power,
  Cpu,
  MoreVertical,
} from "lucide-react";

import ModelStatusBadge from "./ModelStatusBadge";
import { getAlgorithmLabel as formatAlgorithmLabel } from "../types";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getAlgorithmLabel(algorithm) {
  return algorithm ? formatAlgorithmLabel(algorithm) : "—";
}

function getTrainingCount(model) {
  return (
    model.training_run_count ??
    model.training_runs_count ??
    model.training_runs?.length ??
    0
  );
}

function getLatestVersion(model) {
  return (
    model.latest_version?.version ??
    model.latest_version_number ??
    model.latest_version ??
    "—"
  );
}

function ModelRowActions({ model, isActive, updating, onView, onEdit, onToggleStatus }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const menuRef = useRef(null);
  const triggerRef = useRef(null);
  const [position, setPosition] = useState({ top: 0, left: 0, ready: false });

  useEffect(() => {
    if (!open || !triggerRef.current) return undefined;
    const place = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const width = 178;
      const height = menuRef.current?.getBoundingClientRect().height || 128;
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      const top = spaceBelow >= height + 8 || spaceBelow >= spaceAbove
        ? Math.min(rect.bottom + 5, window.innerHeight - height - 8)
        : Math.max(8, rect.top - height - 5);
      setPosition({ top, left: Math.max(8, Math.min(rect.right - width, window.innerWidth - width - 8)), ready: true });
    };
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;
    const closeOutside = (event) => {
      if (!rootRef.current?.contains(event.target) && !menuRef.current?.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  const runAction = (action) => {
    setOpen(false);
    action?.(model);
  };

  return (
    <div className="ml-model-actions-menu" ref={rootRef}>
      <button
        type="button"
        ref={triggerRef}
        className="ml-icon-button ml-model-actions-menu__trigger"
        aria-label={`Actions for ${model.name}`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <MoreVertical size={18} aria-hidden="true" />
      </button>
      {open && createPortal(
        <div ref={menuRef} className="ml-model-actions-menu__popover" role="menu" style={{ top: position.top, left: position.left, visibility: position.ready ? "visible" : "hidden" }}>
          <button className="ml-model-actions-menu__view" type="button" role="menuitem" onClick={() => runAction(onView)}>
            <Eye size={15} /> View details
          </button>
          {onEdit && <button type="button" role="menuitem" onClick={() => runAction(onEdit)}>
            <Pencil size={15} /> Edit model
          </button>}
          {onToggleStatus && <button
            type="button"
            role="menuitem"
            disabled={updating}
            onClick={() => runAction(onToggleStatus)}
          >
            <Power size={15} />
            {updating ? "Updating…" : isActive ? "Deactivate" : "Activate"}
          </button>}
        </div>, document.body
      )}
    </div>
  );
}

export default function ModelTable({
  models = [],
  loading = false,
  error = "",
  onView,
  onEdit,
  onToggleStatus,
  statusUpdatingId,
}) {
  if (loading) {
    return (
      <div className="ml-empty-state">
        <span className="ml-spinner" aria-hidden="true" />
        <p>Loading models...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="ml-empty-state ml-empty-state--error"
        role="alert"
      >
        <p>{error}</p>
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="ml-empty-state">
        <div className="ml-empty-state__icon">
          <Cpu size={22} />
        </div>
        <h3>No models found</h3>
        <p>
          No model definitions match the current filters.
          Create a model or adjust your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="ml-table-wrapper">
      <table className="ml-table">
        <colgroup>
          <col className="ml-models-column--model" />
          <col className="ml-models-column--type" />
          <col className="ml-models-column--algorithm" />
          <col className="ml-models-column--status" />
          <col className="ml-models-column--runs" />
          <col className="ml-models-column--version" />
          <col className="ml-models-column--updated" />
          <col className="ml-models-column--actions" />
        </colgroup>
        <thead>
          <tr>
            <th>Model</th>
            <th>Type</th>
            <th>Algorithm</th>
            <th>Status</th>
            <th>Training Runs</th>
            <th>Latest Version</th>
            <th>Updated At</th>
            <th className="ml-table__actions-heading">
              Actions
            </th>
          </tr>
        </thead>

        <tbody>
          {models.map((model) => {
            const trainingCount = getTrainingCount(model);
            const latestVersion = getLatestVersion(model);
            const isActive = model.status === "active";

            return (
              <tr key={model.id}>
                <td>
                  <div className="ml-model-cell">
                    <div className="ml-model-cell__icon">
                      <span>
                        {(model.name || "M")
                          .charAt(0)
                          .toUpperCase()}
                      </span>
                    </div>

                    <div className="ml-model-cell__content">
                      <strong title={model.name || "Unnamed model"}>
                        {model.name || "Unnamed model"}
                      </strong>
                      <span title={model.description || "No description"}>
                        {model.description || "No description"}
                      </span>
                    </div>
                  </div>
                </td>

                <td>
                  <span className="ml-algorithm-label" title={model.model_type || model.type || "Classifier"}>
                    {model.model_type ||
                      model.type ||
                      "Classifier"}
                  </span>
                </td>

                <td>
                  <span className="ml-algorithm-label" title={getAlgorithmLabel(model.algorithm)}>
                    {getAlgorithmLabel(model.algorithm)}
                  </span>
                </td>

                <td>
                  <ModelStatusBadge status={model.status} />
                </td>

                <td>
                  <span className="ml-table__number">
                    {trainingCount}
                  </span>
                </td>

                <td>
                  <span className="ml-table__version">
                    {latestVersion === "—"
                      ? "—"
                      : `v${latestVersion}`}
                  </span>
                </td>

                <td className="ml-table__date">
                  {formatDate(model.updated_at || model.created_at)}
                </td>

                <td className="ml-model-table__action-cell">
                  <ModelRowActions
                    model={model}
                    isActive={isActive}
                    updating={statusUpdatingId === model.id}
                    onView={onView}
                    onEdit={onEdit}
                    onToggleStatus={onToggleStatus}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
