import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  EMAIL_GROUND_TRUTH_LABELS,
  EMAIL_GROUND_TRUTH_OPTIONS,
  getEmailGroundTruthLabel,
  getEmailSourceLabel,
} from "../types";

import emailService from "../services/emailService";


// ============================================================
// DRAWER MODES
// ============================================================

const DRAWER_MODES = Object.freeze({
  ADD: "add",
  VIEW: "view",
});


// ============================================================
// ADD TABS
// ============================================================

const ADD_TABS = Object.freeze({
  UPLOAD: "upload",
  RAW: "raw",
});


// ============================================================
// DEFAULT FORM STATE
// ============================================================

function createDefaultUploadForm() {
  return {
    groundTruthLabel: EMAIL_GROUND_TRUTH_LABELS.NORMAL,
    files: [],
  };
}


function createDefaultRawForm() {
  return {
    sourceIdentifier: "",
    groundTruthLabel: EMAIL_GROUND_TRUTH_LABELS.NORMAL,
    rawContent: "",
  };
}


// ============================================================
// DATE FORMATTER
// ============================================================

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString();
}


// ============================================================
// SAFE DISPLAY HELPERS
// ============================================================

function displayValue(value) {
  if (
    value === undefined ||
    value === null ||
    value === ""
  ) {
    return "—";
  }

  return String(value);
}


function formatRecipients(value) {
  if (
    value === undefined ||
    value === null ||
    value === ""
  ) {
    return "—";
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return "—";
    }

    return value.join(", ");
  }

  return String(value);
}


function formatFileSize(bytes) {
  if (
    !Number.isFinite(bytes) ||
    bytes <= 0
  ) {
    return "0 B";
  }

  const units = [
    "B",
    "KB",
    "MB",
    "GB",
  ];

  const exponent = Math.min(
    Math.floor(
      Math.log(bytes) /
        Math.log(1024),
    ),
    units.length - 1,
  );

  const size =
    bytes /
    1024 ** exponent;

  return `${size.toFixed(
    exponent === 0 ? 0 : 1,
  )} ${units[exponent]}`;
}


// ============================================================
// DRAWER HEADER
// ============================================================

function DrawerHeader({
  mode,
  onClose,
}) {
  const isViewMode =
    mode === DRAWER_MODES.VIEW;

  return (
    <header className="email-drawer-header">
      <div className="email-drawer-header-content">
        <span className="email-drawer-eyebrow">
          {isViewMode
            ? "EMAIL DETAILS"
            : "EMAIL MANAGEMENT"}
        </span>

        <h2
          id="email-drawer-title"
          className="email-drawer-title"
        >
          {isViewMode
            ? "Email Details"
            : "Add Emails"}
        </h2>

        <p className="email-drawer-subtitle">
          {isViewMode
            ? "Review the collected email and its ground-truth label."
            : "Upload .EML files or add a raw email with a ground-truth label."}
        </p>
      </div>

      <button
        type="button"
        className="email-drawer-close"
        onClick={onClose}
        aria-label="Close email drawer"
      >
        ×
      </button>
    </header>
  );
}


// ============================================================
// GROUND-TRUTH SELECT
// ============================================================

function GroundTruthSelect({
  id,
  value,
  onChange,
  disabled = false,
}) {
  return (
    <div className="email-drawer-field">
      <label
        htmlFor={id}
        className="email-drawer-label"
      >
        Ground Truth Label
        <span aria-hidden="true">
          {" "}
          *
        </span>
      </label>

      <select
        id={id}
        className="email-drawer-input"
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        disabled={disabled}
      >
        {EMAIL_GROUND_TRUTH_OPTIONS.map(
          (option) => (
            <option
              key={option.value}
              value={option.value}
            >
              {option.label}
            </option>
          ),
        )}
      </select>

      <span className="email-drawer-help">
        This label is the ground truth for the
        uploaded email(s).
      </span>
    </div>
  );
}


// ============================================================
// UPLOAD TAB
// ============================================================

function UploadTab({
  form,
  onChange,
  onSubmit,
  submitting,
  error,
  success,
}) {
  const fileInputRef = useRef(null);

  function handleFileChange(event) {
    const selectedFiles = Array.from(
      event.target.files || [],
    );

    onChange({
      ...form,
      files: selectedFiles,
    });
  }


  function removeFile(index) {
    onChange({
      ...form,
      files: form.files.filter(
        (_, fileIndex) =>
          fileIndex !== index,
      ),
    });
  }


  function clearFiles() {
    onChange({
      ...form,
      files: [],
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }


  return (
    <form
      className="email-drawer-form"
      onSubmit={onSubmit}
    >
      <div className="email-drawer-field">
        <label
          htmlFor="email-eml-files"
          className="email-drawer-label"
        >
          Email Files
          <span aria-hidden="true">
            {" "}
            *
          </span>
        </label>

        <input
          ref={fileInputRef}
          id="email-eml-files"
          type="file"
          accept=".eml,message/rfc822"
          multiple
          className="email-drawer-file-input"
          onChange={handleFileChange}
          disabled={submitting}
        />

        <span className="email-drawer-help">
          Select one or more .EML files.
          Every file in this batch receives
          the same ground-truth label.
        </span>
      </div>

      <GroundTruthSelect
        id="upload-ground-truth-label"
        value={form.groundTruthLabel}
        onChange={(groundTruthLabel) =>
          onChange({
            ...form,
            groundTruthLabel,
          })
        }
        disabled={submitting}
      />

      {form.files.length > 0 && (
        <div className="email-drawer-file-list">
          <div className="email-drawer-file-list-header">
            <strong>
              Selected Files
            </strong>

            <button
              type="button"
              className="email-drawer-text-button"
              onClick={clearFiles}
              disabled={submitting}
            >
              Clear
            </button>
          </div>

          {form.files.map(
            (file, index) => (
              <div
                className="email-drawer-file-item"
                key={`${file.name}-${index}`}
              >
                <div className="email-drawer-file-info">
                  <span className="email-drawer-file-name">
                    {file.name}
                  </span>

                  <span className="email-drawer-file-size">
                    {formatFileSize(
                      file.size,
                    )}
                  </span>
                </div>

                <button
                  type="button"
                  className="email-drawer-file-remove"
                  onClick={() =>
                    removeFile(index)
                  }
                  disabled={submitting}
                  aria-label={`Remove ${file.name}`}
                >
                  ×
                </button>
              </div>
            ),
          )}
        </div>
      )}

      {error && (
        <div
          className="email-drawer-message email-drawer-error"
          role="alert"
        >
          {error}
        </div>
      )}

      {success && (
        <div
          className="email-drawer-message email-drawer-success"
          role="status"
        >
          {success}
        </div>
      )}

      <div className="email-drawer-footer">
        <button
          type="submit"
          className="email-primary-button"
          disabled={
            submitting ||
            form.files.length === 0
          }
        >
          {submitting
            ? "Uploading..."
            : form.files.length > 1
              ? `Upload ${form.files.length} Emails`
              : "Upload Email"}
        </button>
      </div>
    </form>
  );
}


// ============================================================
// RAW EMAIL TAB
// ============================================================

function RawEmailTab({
  form,
  onChange,
  onSubmit,
  submitting,
  error,
  success,
}) {
  return (
    <form
      className="email-drawer-form"
      onSubmit={onSubmit}
    >
      <div className="email-drawer-field">
        <label
          htmlFor="raw-source-identifier"
          className="email-drawer-label"
        >
          Source Identifier
        </label>

        <input
          id="raw-source-identifier"
          type="text"
          className="email-drawer-input"
          value={form.sourceIdentifier}
          onChange={(event) =>
            onChange({
              ...form,
              sourceIdentifier:
                event.target.value,
            })
          }
          placeholder="Optional source identifier"
          maxLength={512}
          disabled={submitting}
        />

        <span className="email-drawer-help">
          Optional identifier for the source of
          this raw email.
        </span>
      </div>

      <GroundTruthSelect
        id="raw-ground-truth-label"
        value={form.groundTruthLabel}
        onChange={(groundTruthLabel) =>
          onChange({
            ...form,
            groundTruthLabel,
          })
        }
        disabled={submitting}
      />

      <div className="email-drawer-field">
        <label
          htmlFor="raw-email-content"
          className="email-drawer-label"
        >
          Raw Email Content
          <span aria-hidden="true">
            {" "}
            *
          </span>
        </label>

        <textarea
          id="raw-email-content"
          className="email-drawer-textarea"
          value={form.rawContent}
          onChange={(event) =>
            onChange({
              ...form,
              rawContent:
                event.target.value,
            })
          }
          placeholder="Paste the complete raw email including headers..."
          rows={18}
          disabled={submitting}
        />

        <span className="email-drawer-help">
          Include the complete raw email content,
          including its headers.
        </span>
      </div>

      {error && (
        <div
          className="email-drawer-message email-drawer-error"
          role="alert"
        >
          {error}
        </div>
      )}

      {success && (
        <div
          className="email-drawer-message email-drawer-success"
          role="status"
        >
          {success}
        </div>
      )}

      <div className="email-drawer-footer">
        <button
          type="submit"
          className="email-primary-button"
          disabled={
            submitting ||
            !form.rawContent.trim()
          }
        >
          {submitting
            ? "Adding..."
            : "Add Email"}
        </button>
      </div>
    </form>
  );
}


// ============================================================
// DETAIL SECTION
// ============================================================

function DetailSection({
  eyebrow,
  title,
  children,
}) {
  return (
    <section className="email-drawer-detail-section">
      <div className="email-drawer-detail-section-header">
        <div>
          <span className="email-drawer-section-eyebrow">
            {eyebrow}
          </span>

          <h3 className="email-drawer-section-title">
            {title}
          </h3>
        </div>
      </div>

      {children}
    </section>
  );
}


// ============================================================
// DETAIL ROW
// ============================================================

function DetailRow({
  label,
  value,
  valueClassName = "",
}) {
  return (
    <div className="email-drawer-detail-row">
      <dt className="email-drawer-detail-label">
        {label}
      </dt>

      <dd
        className={`email-drawer-detail-value ${valueClassName}`.trim()}
      >
        {value}
      </dd>
    </div>
  );
}


// ============================================================
// EMAIL DETAIL
// ============================================================

function EmailDetail({
  email,
}) {
  if (!email) {
    return (
      <div className="email-drawer-state">
        <span>
          No email selected.
        </span>
      </div>
    );
  }

  const normalizedGroundTruth =
    String(
      email.ground_truth_label ||
        "unknown",
    ).toLowerCase();

  const groundTruthLabel =
    getEmailGroundTruthLabel(
      email.ground_truth_label,
    );

  const sourceLabel =
    getEmailSourceLabel(
      email.source,
    );

  return (
    <div className="email-drawer-detail">

      {/* ======================================================
          1. GROUND TRUTH
      ======================================================= */}

      <DetailSection
        eyebrow="GROUND TRUTH"
        title="Classification Label"
      >
        <dl className="email-drawer-detail-list">
          <DetailRow
            label="Label"
            value={
              <span
                className={`email-status-badge email-status-${normalizedGroundTruth}`}
              >
                {groundTruthLabel}
              </span>
            }
          />
        </dl>
      </DetailSection>


      {/* ======================================================
          2. SOURCE
      ======================================================= */}

      <DetailSection
        eyebrow="SOURCE"
        title="Collection Source"
      >
        <dl className="email-drawer-detail-list">
          <DetailRow
            label="Source"
            value={
              <span className="email-source-badge">
                {sourceLabel}
              </span>
            }
          />

          <DetailRow
            label="Source Identifier"
            value={displayValue(
              email.source_identifier,
            )}
            valueClassName="email-drawer-monospace"
          />
        </dl>
      </DetailSection>


      {/* ======================================================
          3. BASIC MESSAGE INFORMATION
      ======================================================= */}

      <DetailSection
        eyebrow="MESSAGE"
        title="Message Information"
      >
        <dl className="email-drawer-detail-list">
          <DetailRow
            label="Subject"
            value={displayValue(
              email.subject,
            )}
          />

          <DetailRow
            label="Sender"
            value={displayValue(
              email.sender,
            )}
          />

          <DetailRow
            label="Recipients"
            value={formatRecipients(
              email.recipients,
            )}
          />

          <DetailRow
            label="CC"
            value={formatRecipients(
              email.cc,
            )}
          />

          <DetailRow
            label="BCC"
            value={formatRecipients(
              email.bcc,
            )}
          />

          <DetailRow
            label="Reply-To"
            value={displayValue(
              email.reply_to,
            )}
          />

          <DetailRow
            label="Message-ID"
            value={displayValue(
              email.message_id,
            )}
            valueClassName="email-drawer-monospace"
          />
        </dl>
      </DetailSection>


      {/* ======================================================
          4. TIME INFORMATION
      ======================================================= */}

      <DetailSection
        eyebrow="TIME"
        title="Time Information"
      >
        <dl className="email-drawer-detail-list">
          <DetailRow
            label="Received"
            value={formatDate(
              email.received_at,
            )}
          />

          <DetailRow
            label="Collected At"
            value={formatDate(
              email.collected_at,
            )}
          />
        </dl>
      </DetailSection>


      {/* ======================================================
          5. EMAIL TECHNICAL INFORMATION
      ======================================================= */}

      <DetailSection
        eyebrow="TECHNICAL"
        title="Email Technical Information"
      >
        <dl className="email-drawer-detail-list">

          <DetailRow
            label="Content Type"
            value={displayValue(
              email.content_type,
            )}
            valueClassName="email-drawer-monospace"
          />

          <DetailRow
            label="MIME Version"
            value={displayValue(
              email.mime_version,
            )}
            valueClassName="email-drawer-monospace"
          />

          <DetailRow
            label="Content Hash"
            value={displayValue(
              email.content_hash,
            )}
            valueClassName="email-drawer-monospace"
          />

          <DetailRow
            label="Email ID"
            value={displayValue(
              email.id,
            )}
            valueClassName="email-drawer-monospace"
          />

        </dl>
      </DetailSection>


      {/* ======================================================
          6. EMAIL CONTENT
      ======================================================= */}

      <DetailSection
        eyebrow="CONTENT"
        title="Email Content"
      >
        <div className="email-drawer-content-wrapper">
          <pre className="email-drawer-content">
            {displayValue(
              email.raw_content,
            )}
          </pre>
        </div>
      </DetailSection>

    </div>
  );
}


// ============================================================
// MAIN EMAIL DRAWER
// ============================================================

export default function EmailDrawer({
  mode = DRAWER_MODES.ADD,
  email = null,
  initialTab = ADD_TABS.UPLOAD,
  onClose,
  onCreated,
  onUpload,
  onRawSubmit,
  onSuccess,
  loading = false,
}) {
  const [activeTab, setActiveTab] =
    useState(initialTab);

  const [
    uploadForm,
    setUploadForm,
  ] = useState(
    createDefaultUploadForm,
  );

  const [
    rawForm,
    setRawForm,
  ] = useState(
    createDefaultRawForm,
  );

  const [
    submitting,
    setSubmitting,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    success,
    setSuccess,
  ] = useState("");


  // ==========================================================
  // RESET STATE WHEN DRAWER CONTEXT CHANGES
  // ==========================================================

  useEffect(() => {
    setActiveTab(
      initialTab || ADD_TABS.UPLOAD,
    );

    setUploadForm(
      createDefaultUploadForm(),
    );

    setRawForm(
      createDefaultRawForm(),
    );

    setSubmitting(false);
    setError("");
    setSuccess("");
  }, [
    initialTab,
    email?.id,
    mode,
  ]);


  // ==========================================================
  // ESCAPE KEY
  // ==========================================================

  useEffect(() => {
    function handleKeyDown(event) {
      if (
        event.key === "Escape" &&
        !submitting
      ) {
        onClose?.();
      }
    }

    window.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [
    submitting,
    onClose,
  ]);


  // ==========================================================
  // BODY SCROLL LOCK
  // ==========================================================

  useEffect(() => {
    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      "hidden";

    return () => {
      document.body.style.overflow =
        previousOverflow;
    };
  }, []);


  const isViewMode =
    mode === DRAWER_MODES.VIEW;


  // ==========================================================
  // SUCCESS HANDLER
  // ==========================================================

  function notifySuccess(result) {
    onCreated?.(result);
    onSuccess?.(result);
  }


  // ==========================================================
  // UPLOAD SUBMIT
  // ==========================================================

  async function handleUploadSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (
      uploadForm.files.length === 0
    ) {
      setError(
        "Please select at least one .eml file.",
      );
      return;
    }

    if (
      !uploadForm.groundTruthLabel
    ) {
      setError(
        "Please select a ground-truth label.",
      );
      return;
    }

    setSubmitting(true);

    try {
      let result;

      if (
        uploadForm.files.length === 1
      ) {
        result =
          await emailService.uploadEmail(
            uploadForm.files[0],
            uploadForm.groundTruthLabel,
          );
      } else {
        result =
          await emailService.uploadEmailsBulk(
            uploadForm.files,
            uploadForm.groundTruthLabel,
          );
      }

      setSuccess(
        uploadForm.files.length === 1
          ? "Email uploaded successfully."
          : "Email batch uploaded successfully.",
      );

      notifySuccess(result);
      onUpload?.(result);

      setUploadForm(
        createDefaultUploadForm(),
      );
    } catch (submitError) {
      setError(
        submitError?.message ||
          "Failed to upload email.",
      );
    } finally {
      setSubmitting(false);
    }
  }


  // ==========================================================
  // RAW EMAIL SUBMIT
  // ==========================================================

  async function handleRawSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (
      !rawForm.rawContent.trim()
    ) {
      setError(
        "Raw email content is required.",
      );
      return;
    }

    if (
      !rawForm.groundTruthLabel
    ) {
      setError(
        "Please select a ground-truth label.",
      );
      return;
    }

    setSubmitting(true);

    try {
      const result =
        await emailService.ingestEmail({
          sourceIdentifier:
            rawForm.sourceIdentifier.trim() ||
            null,

          groundTruthLabel:
            rawForm.groundTruthLabel,

          rawContent:
            rawForm.rawContent,
        });

      setSuccess(
        "Email added successfully.",
      );

      notifySuccess(result);
      onRawSubmit?.(result);

      setRawForm(
        createDefaultRawForm(),
      );
    } catch (submitError) {
      setError(
        submitError?.message ||
          "Failed to add email.",
      );
    } finally {
      setSubmitting(false);
    }
  }


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div
      className="email-drawer-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target ===
            event.currentTarget &&
          !submitting
        ) {
          onClose?.();
        }
      }}
    >
      <aside
        className="email-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="email-drawer-title"
        onMouseDown={(event) =>
          event.stopPropagation()
        }
      >
        <DrawerHeader
          mode={mode}
          onClose={onClose}
        />

        {loading ? (
          <div
            className="email-drawer-state"
            role="status"
            aria-live="polite"
          >
            <div
              className="email-loading-indicator"
              aria-hidden="true"
            />

            <span>
              Loading email details...
            </span>
          </div>
        ) : isViewMode ? (
          <EmailDetail
            email={email}
          />
        ) : (
          <>
            <div
              className="email-drawer-tabs"
              role="tablist"
              aria-label="Add email method"
            >
              <button
                type="button"
                role="tab"
                aria-selected={
                  activeTab ===
                  ADD_TABS.UPLOAD
                }
                className={`email-drawer-tab ${
                  activeTab ===
                  ADD_TABS.UPLOAD
                    ? "is-active"
                    : ""
                }`}
                onClick={() => {
                  if (submitting) {
                    return;
                  }

                  setActiveTab(
                    ADD_TABS.UPLOAD,
                  );

                  setError("");
                  setSuccess("");
                }}
              >
                Upload .EML
              </button>

              <button
                type="button"
                role="tab"
                aria-selected={
                  activeTab ===
                  ADD_TABS.RAW
                }
                className={`email-drawer-tab ${
                  activeTab ===
                  ADD_TABS.RAW
                    ? "is-active"
                    : ""
                }`}
                onClick={() => {
                  if (submitting) {
                    return;
                  }

                  setActiveTab(
                    ADD_TABS.RAW,
                  );

                  setError("");
                  setSuccess("");
                }}
              >
                Raw Email
              </button>
            </div>

            {activeTab ===
              ADD_TABS.UPLOAD && (
              <UploadTab
                form={uploadForm}
                onChange={
                  setUploadForm
                }
                onSubmit={
                  handleUploadSubmit
                }
                submitting={
                  submitting
                }
                error={error}
                success={success}
              />
            )}

            {activeTab ===
              ADD_TABS.RAW && (
              <RawEmailTab
                form={rawForm}
                onChange={
                  setRawForm
                }
                onSubmit={
                  handleRawSubmit
                }
                submitting={
                  submitting
                }
                error={error}
                success={success}
              />
            )}
          </>
        )}
      </aside>
    </div>
  );
}


// ============================================================
// EXPORT DRAWER CONSTANTS
// ============================================================

export {
  ADD_TABS,
  DRAWER_MODES,
};