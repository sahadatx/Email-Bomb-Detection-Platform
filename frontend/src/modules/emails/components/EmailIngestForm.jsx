import { useState } from "react";

import emailService from "../services/emailService";

import {
  EMAIL_GROUND_TRUTH_LABELS,
  EMAIL_GROUND_TRUTH_OPTIONS,
} from "../types";


const INITIAL_FORM = {
  sourceIdentifier: "",
  groundTruthLabel:
    EMAIL_GROUND_TRUTH_LABELS.NORMAL,
  rawContent: "",
};


export default function EmailIngestForm({
  onSuccess,
  onError,
}) {
  const [form, setForm] = useState(
    INITIAL_FORM,
  );

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");


  // ==========================================================
  // FORM CHANGE
  // ==========================================================

  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    if (error) {
      setError("");
    }

    if (success) {
      setSuccess("");
    }
  }


  // ==========================================================
  // VALIDATION
  // ==========================================================

  function validateForm() {
    const sourceIdentifier =
      form.sourceIdentifier.trim();

    const rawContent =
      form.rawContent.trim();

    if (!rawContent) {
      return "Raw email content is required.";
    }

    if (
      !form.groundTruthLabel
    ) {
      return "Ground-truth label is required.";
    }

    if (
      form.sourceIdentifier.length >
      512
    ) {
      return (
        "Source identifier must not exceed 512 characters."
      );
    }

    return null;
  }


  // ==========================================================
  // SUBMIT
  // ==========================================================

  async function handleSubmit(event) {
    event.preventDefault();

    const validationError =
      validateForm();

    if (validationError) {
      setError(validationError);
      setSuccess("");
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const response =
        await emailService.ingestEmail({
          sourceIdentifier:
            form.sourceIdentifier.trim() ||
            null,

          groundTruthLabel:
            form.groundTruthLabel,

          rawContent:
            form.rawContent.trim(),
        });

      setForm(
        INITIAL_FORM,
      );

      setSuccess(
        "Email was successfully added.",
      );

      onSuccess?.(response);
    } catch (requestError) {
      const message =
        requestError?.message ||
        "Unable to add the email.";

      setError(message);

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

    setForm(
      INITIAL_FORM,
    );

    setError("");
    setSuccess("");
  }


  const hasContent =
    form.sourceIdentifier.trim() ||
    form.rawContent.trim();


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <form
      className="email-ingest-form"
      onSubmit={handleSubmit}
      noValidate
    >
      {/* ====================================================
          HEADER
          ==================================================== */}

      <div className="email-form-header">
        <div>
          <h2>
            Add Raw Email
          </h2>

          <p>
            Add a complete raw email message
            directly to Email Management.
          </p>
        </div>

        <span className="email-form-source-badge">
          RAW EMAIL
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
            Ingestion failed
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
            Ingestion successful
          </strong>

          <span>
            {success}
          </span>
        </div>
      )}


      {/* ====================================================
          SOURCE IDENTIFIER
          ==================================================== */}

      <div className="email-form-field">
        <label
          htmlFor="email-source-identifier"
        >
          Source Identifier

          <span className="email-form-optional">
            Optional
          </span>
        </label>

        <input
          id="email-source-identifier"
          name="sourceIdentifier"
          type="text"
          value={
            form.sourceIdentifier
          }
          onChange={
            handleChange
          }
          maxLength={512}
          placeholder="e.g. manual-import-001"
          autoComplete="off"
          disabled={submitting}
        />

        <span className="email-form-help">
          Optional identifier used to trace
          where this email came from.
        </span>
      </div>


      {/* ====================================================
          GROUND TRUTH
          ==================================================== */}

      <div className="email-form-field">
        <label
          htmlFor="email-ground-truth-label"
        >
          Ground Truth Label

          <span className="email-form-required">
            Required
          </span>
        </label>

        <select
          id="email-ground-truth-label"
          name="groundTruthLabel"
          value={
            form.groundTruthLabel
          }
          onChange={
            handleChange
          }
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
          This is the ground-truth label for
          this email. It is not a prediction.
        </span>
      </div>


      {/* ====================================================
          RAW CONTENT
          ==================================================== */}

      <div className="email-form-field">
        <label
          htmlFor="email-raw-content"
        >
          Raw Email Content

          <span className="email-form-required">
            Required
          </span>
        </label>

        <textarea
          id="email-raw-content"
          name="rawContent"
          value={
            form.rawContent
          }
          onChange={
            handleChange
          }
          placeholder={`From: sender@example.com
To: recipient@example.com
Subject: Example email
Date: Wed, 23 Sep 2026 10:00:00 +0000
Message-ID: <example@example.com>
Content-Type: text/plain; charset="UTF-8"

Email body goes here...`}
          rows={20}
          spellCheck={false}
          disabled={submitting}
          required
        />

        <span className="email-form-help">
          Include the complete email headers and
          body.
        </span>
      </div>


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
            !hasContent
          }
        >
          Reset
        </button>

        <button
          type="submit"
          className="email-primary-button"
          disabled={submitting}
        >
          {submitting
            ? "Adding..."
            : "Add Email"}
        </button>
      </div>
    </form>
  );
}