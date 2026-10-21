
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import {
  X,
  Database,
  Mail,
  ShieldAlert,
  FileText,
  Layers,
  AlertCircle,
} from "lucide-react";

const INITIAL_FORM = {
  name: "",
  description: "",
};

function getCount(value) {
  const count = Number(value);
  return Number.isFinite(count) && count >= 0 ? count : 0;
}

export default function DatasetCreateModal({
  open = false,
  selectedCount = 0,
  normalCount = 0,
  bombingCount = 0,
  featureSchema = [],
  submitting = false,
  error = null,
  onClose,
  onSubmit,
  className = "",
}) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    if (open) {
      setForm(INITIAL_FORM);
      setValidationError("");
    }
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === "Escape" && !submitting) {
        onClose?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, submitting, onClose]);

  if (!open) return null;

  const safeSelectedCount = getCount(selectedCount);
  const safeNormalCount = getCount(normalCount);
  const safeBombingCount = getCount(bombingCount);

  const normalizedName = form.name.trim();
  const canSubmit =
    normalizedName.length > 0 &&
    safeSelectedCount > 0 &&
    !submitting;

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    if (validationError) {
      setValidationError("");
    }
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (!normalizedName) {
      setValidationError("Dataset name is required.");
      return;
    }

    if (safeSelectedCount < 1) {
      setValidationError("Select at least one email.");
      return;
    }

    setValidationError("");

    onSubmit?.({
      name: normalizedName,
      description: form.description.trim(),
    });
  }

  return createPortal((
    <div
      className="dataset-create-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !submitting) {
          onClose?.();
        }
      }}
    >
      <section
        className={`dataset-create-modal ${className}`.trim()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dataset-create-title"
      >
        <header className="dataset-create-modal__header">
          <div className="dataset-create-modal__heading">
            <div className="dataset-create-modal__icon">
              <Database size={21} />
            </div>

            <div>
              <h2 id="dataset-create-title">
                Create Dataset
              </h2>
              <p>
                Create a dataset from the selected eligible emails.
              </p>
            </div>
          </div>

          <button
            type="button"
            className="dataset-icon-button"
            onClick={onClose}
            disabled={submitting}
            aria-label="Close create dataset dialog"
          >
            <X size={20} />
          </button>
        </header>

        <form onSubmit={handleSubmit}>
          <div className="dataset-create-modal__body">
            <section className="dataset-create-summary">
              <div className="dataset-create-summary__heading">
                <Layers size={17} />
                <h3>Selection Summary</h3>
              </div>

              <div className="dataset-create-summary__grid">
                <div className="dataset-create-summary__item">
                  <span className="dataset-create-summary__icon dataset-create-summary__icon--total">
                    <Mail size={18} />
                  </span>
                  <div>
                    <strong>
                      {safeSelectedCount.toLocaleString()}
                    </strong>
                    <span>Dataset Emails</span>
                  </div>
                </div>

                <div className="dataset-create-summary__item">
                  <span className="dataset-create-summary__icon dataset-create-summary__icon--normal">
                    <Mail size={18} />
                  </span>
                  <div>
                    <strong>
                      {safeNormalCount.toLocaleString()}
                    </strong>
                    <span>Normal</span>
                  </div>
                </div>

                <div className="dataset-create-summary__item">
                  <span className="dataset-create-summary__icon dataset-create-summary__icon--bombing">
                    <ShieldAlert size={18} />
                  </span>
                  <div>
                    <strong>
                      {safeBombingCount.toLocaleString()}
                    </strong>
                    <span>Bombing</span>
                  </div>
                </div>
              </div>
            </section>

            <div className="dataset-form-field">
              <label htmlFor="dataset-name">
                Dataset Name <span aria-hidden="true">*</span>
              </label>

              <input
                id="dataset-name"
                name="name"
                type="text"
                value={form.name}
                onChange={handleChange}
                placeholder="e.g. Email Bomb Detection Dataset"
                maxLength={120}
                required
                autoFocus
                disabled={submitting}
              />

              <small>
                Use a clear name to identify this dataset.
              </small>
            </div>

            <div className="dataset-form-field">
              <label htmlFor="dataset-description">
                Description
              </label>

              <textarea
                id="dataset-description"
                name="description"
                value={form.description}
                onChange={handleChange}
                placeholder="Describe the purpose or contents of this dataset..."
                rows={4}
                maxLength={1000}
                disabled={submitting}
              />

              <small>
                {form.description.length}/1000 characters
              </small>
            </div>

            <section className="dataset-create-schema">
              <div className="dataset-create-schema__heading">
                <FileText size={17} />
                <div>
                  <h3>Feature Schema</h3>
                  <p>
                    Canonical features available for this dataset.
                  </p>
                </div>
              </div>

              {featureSchema.length > 0 ? (
                <div className="dataset-create-schema__list">
                  {featureSchema.map((feature, index) => {
                    const code =
                      typeof feature === "string"
                        ? feature
                        : feature.code ??
                          feature.key ??
                          feature.name ??
                          `F${index + 1}`;

                    const label =
                      typeof feature === "string"
                        ? feature
                        : feature.label ??
                          feature.description ??
                          feature.name ??
                          code;

                    return (
                      <div
                        className="dataset-create-schema__item"
                        key={`${code}-${index}`}
                      >
                        <code>{code}</code>
                        <span>{label}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="dataset-create-schema__empty">
                  Feature schema will be loaded from the dataset
                  configuration.
                </p>
              )}
            </section>

            {(validationError || error) && (
              <div
                className="dataset-form-error"
                role="alert"
              >
                <AlertCircle size={17} />
                <span>{validationError || error}</span>
              </div>
            )}
          </div>

          <footer className="dataset-create-modal__footer">
            <button
              type="button"
              className="dataset-button dataset-button--secondary"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="dataset-button dataset-button--primary"
              disabled={!canSubmit}
            >
              {submitting ? (
                <>
                  <span className="dataset-spinner dataset-spinner--small" />
                  Creating...
                </>
              ) : (
                <>
                  <Database size={16} />
                  Create Dataset
                </>
              )}
            </button>
          </footer>
        </form>
      </section>
    </div>
  ), document.body);
}
