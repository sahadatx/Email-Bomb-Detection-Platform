import {
  useRef,
  useState,
} from "react";

import emailService from "../services/emailService";

import {
  EMAIL_GROUND_TRUTH_LABELS,
  EMAIL_GROUND_TRUTH_OPTIONS,
} from "../types";


const MAX_FILE_SIZE =
  25 * 1024 * 1024;


export default function EmailUploadForm({
  onSuccess,
  onError,
}) {
  const fileInputRef =
    useRef(null);

  const [files, setFiles] =
    useState([]);

  const [groundTruthLabel, setGroundTruthLabel] =
    useState(
      EMAIL_GROUND_TRUTH_LABELS.NORMAL,
    );

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const [hasPartialFailure, setHasPartialFailure] =
    useState(false);


  // ==========================================================
  // FILE VALIDATION
  // ==========================================================

  function validateFile(file) {
    if (!file) {
      return "Invalid email file.";
    }

    if (
      !file.name
        .toLowerCase()
        .endsWith(".eml")
    ) {
      return (
        `"${file.name}" is not an .eml file.`
      );
    }

    if (file.size === 0) {
      return (
        `"${file.name}" is empty.`
      );
    }

    if (
      file.size > MAX_FILE_SIZE
    ) {
      return (
        `"${file.name}" exceeds the 25 MB limit.`
      );
    }

    return null;
  }


  // ==========================================================
  // FILE CHANGE
  // ==========================================================

  function handleFileChange(event) {
    const selectedFiles =
      Array.from(
        event.target.files || [],
      );

    setError("");
    setSuccess("");
    setHasPartialFailure(false);

    if (
      selectedFiles.length === 0
    ) {
      setFiles([]);
      return;
    }

    const validationErrors =
      selectedFiles
        .map(validateFile)
        .filter(Boolean);

    if (
      validationErrors.length > 0
    ) {
      setFiles([]);

      setError(
        validationErrors[0],
      );

      event.target.value = "";

      return;
    }

    setFiles(
      selectedFiles,
    );
  }


  // ==========================================================
  // REMOVE FILE
  // ==========================================================

  function handleRemoveFile(
    index,
  ) {
    if (submitting) {
      return;
    }

    setFiles(
      (currentFiles) =>
        currentFiles.filter(
          (_, currentIndex) =>
            currentIndex !== index,
        ),
    );

    setError("");
    setSuccess("");
    setHasPartialFailure(false);
  }


  // ==========================================================
  // SUBMIT
  // ==========================================================

  async function handleSubmit(event) {
    event.preventDefault();

    if (
      files.length === 0
    ) {
      setError(
        "Please select at least one .eml file.",
      );

      return;
    }

    if (
      !groundTruthLabel
    ) {
      setError(
        "Ground-truth label is required.",
      );

      return;
    }

    setSubmitting(true);
    setError("");
    setSuccess("");
    setHasPartialFailure(false);

    try {
      let response;

      if (
        files.length === 1
      ) {
        response =
          await emailService.uploadEmail(
            files[0],
            groundTruthLabel,
          );
      } else {
        response =
          await emailService.uploadEmailsBulk(
            files,
            groundTruthLabel,
          );
      }

      if (files.length > 1) {
        const failedNames = new Set(
          (response.items || [])
            .filter((item) => item.error && !item.duplicate)
            .map((item) => item.filename),
        );
        const failedFiles = files.filter((file) => failedNames.has(file.name));

        setFiles(failedFiles);
        if (fileInputRef.current) fileInputRef.current.value = "";

        setSuccess(
          `${response.successful} uploaded, ${response.duplicates} already existed, and ${response.failed} failed out of ${response.total_files} files.`,
        );

        if (response.failed > 0) {
        setHasPartialFailure(true);
        setError(
            `Could not process: ${[...failedNames].join(", ") || `${response.failed} file(s)`}. The failed files remain selected so you can retry them.`,
        );
        }
      } else {
        setFiles([]);
        if (fileInputRef.current) fileInputRef.current.value = "";
        setSuccess("Email was successfully uploaded and stored.");
      }

      onSuccess?.(
        response,
      );
    } catch (requestError) {
      const message =
        requestError?.message ||
        "Unable to upload the email files.";

      setError(
        message,
      );

      onError?.(
        requestError,
      );
    } finally {
      setSubmitting(false);
    }
  }


  // ==========================================================
  // RESET
  // ==========================================================

  function handleReset() {
    if (submitting) {
      return;
    }

    setFiles([]);

    setGroundTruthLabel(
      EMAIL_GROUND_TRUTH_LABELS.NORMAL,
    );

      setError("");
      setSuccess("");
      setHasPartialFailure(false);

    if (fileInputRef.current) {
      fileInputRef.current.value =
        "";
    }
  }


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <form
      className="email-upload-form"
      onSubmit={handleSubmit}
      noValidate
    >
      {/* ====================================================
          HEADER
          ==================================================== */}

      <div className="email-form-header">
        <div>
          <h2>
            Upload Email Files
          </h2>

          <p>
            Upload one or more RFC-style
            emails saved as
            <strong> .eml </strong>
            files.
          </p>
        </div>

        <span className="email-form-source-badge">
          .EML
        </span>
      </div>


      {/* ====================================================
          ERROR
          ==================================================== */}

      {error && (
        <div
          className="email-form-alert email-form-alert-error"
          role="alert"
        >
          <strong>
            {hasPartialFailure ? "Some files need attention" : "Upload failed"}
          </strong>

          <span>
            {error}
          </span>
        </div>
      )}


      {/* ====================================================
          SUCCESS
          ==================================================== */}

      {success && (
        <div
          className="email-form-alert email-form-alert-success"
          role="status"
        >
          <strong>
            {hasPartialFailure ? "Batch upload finished with errors" : "Upload successful"}
          </strong>

          <span>
            {success}
          </span>
        </div>
      )}


      {/* ====================================================
          GROUND TRUTH
          ==================================================== */}

      <div className="email-form-field">
        <label
          htmlFor="email-upload-ground-truth"
        >
          Ground Truth Label

          <span className="email-form-required">
            Required
          </span>
        </label>

        <select
          id="email-upload-ground-truth"
          value={
            groundTruthLabel
          }
          onChange={(event) => {
            setGroundTruthLabel(
              event.target.value,
            );

    setError("");
    setSuccess("");
    setHasPartialFailure(false);
          }}
          disabled={submitting}
          required
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

        <span className="email-form-help">
          Every file in this upload batch
          receives the selected label.
        </span>
      </div>


      {/* ====================================================
          UPLOAD DROPZONE
          ==================================================== */}

      <div className="email-upload-dropzone">
        <div
          className="email-upload-icon"
          aria-hidden="true"
        >
          ↑
        </div>

        <div className="email-upload-content">
          <strong>
            Select email files
          </strong>

          <span>
            Supported format: .eml ·
            Maximum size: 25 MB per file
          </span>
        </div>

        <label
          htmlFor="email-file-upload"
          className="email-primary-button email-upload-select-button"
        >
          Choose Files
        </label>

        <input
          ref={fileInputRef}
          id="email-file-upload"
          type="file"
          accept=".eml,message/rfc822"
          multiple
          onChange={
            handleFileChange
          }
          disabled={submitting}
          hidden
        />
      </div>


      {/* ====================================================
          SELECTED FILES
          ==================================================== */}

      {files.length > 0 && (
        <div className="email-selected-file-list">
          <div className="email-selected-file-list-header">
            <strong>
              Selected Files
            </strong>

            <span>
              {files.length}
            </span>
          </div>

          {files.map(
            (file, index) => (
              <div
                key={`${file.name}-${file.lastModified}-${index}`}
                className="email-selected-file"
              >
                <div className="email-selected-file-info">
                  <span
                    className="email-selected-file-icon"
                    aria-hidden="true"
                  >
                    ✉
                  </span>

                  <div>
                    <strong>
                      {file.name}
                    </strong>

                    <span>
                      {formatFileSize(
                        file.size,
                      )}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  className="email-file-remove-button"
                  onClick={() =>
                    handleRemoveFile(
                      index,
                    )
                  }
                  disabled={
                    submitting
                  }
                  aria-label={`Remove ${file.name}`}
                >
                  ×
                </button>
              </div>
            ),
          )}
        </div>
      )}


      {/* ====================================================
          ACTIONS
          ==================================================== */}

      <div className="email-form-actions">
        <button
          type="button"
          className="email-secondary-button"
          onClick={handleReset}
          disabled={
            submitting ||
            files.length === 0
          }
        >
          Reset
        </button>

        <button
          type="submit"
          className="email-primary-button"
          disabled={
            submitting ||
            files.length === 0
          }
        >
          {submitting
            ? "Uploading..."
            : files.length > 1
              ? `Upload ${files.length} Emails`
              : "Upload & Ingest"}
        </button>
      </div>
    </form>
  );
}


// ============================================================
// FILE SIZE FORMATTER
// ============================================================

function formatFileSize(
  bytes,
) {
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
    exponent === 0
      ? 0
      : 1,
  )} ${units[exponent]}`;
}
