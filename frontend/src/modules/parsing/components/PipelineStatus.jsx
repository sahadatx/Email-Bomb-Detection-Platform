const PIPELINE_STEPS = Object.freeze([
  {
    id: "collection",
    module: "Module 02",
    label: "Collection",
    description:
      "Email collected by the ingestion pipeline.",
  },
  {
    id: "raw-email",
    module: "Module 02",
    label: "Raw Email Available",
    description:
      "Original MIME content is available as the parsing source.",
  },
  {
    id: "parsing",
    module: "Module 03",
    label: "Parsing",
    description:
      "MIME headers, addresses and message parts are extracted.",
  },
  {
    id: "normalization",
    module: "Module 03",
    label: "Normalization",
    description:
      "Extracted values are normalized into a consistent representation.",
  },
  {
    id: "validation",
    module: "Module 03",
    label: "Validation",
    description:
      "Parsed content is checked for structural validity.",
  },
  {
    id: "features",
    module: "Module 04",
    label: "Feature Extraction",
    description:
      "Ready for downstream feature engineering.",
  },
]);

function normalizeStatus(status) {
  const value = String(
    status || "",
  ).toLowerCase();

  if (
    value === "parsed" ||
    value === "warning" ||
    value === "failed"
  ) {
    return value;
  }

  return "pending";
}

function getSteps(status) {
  const normalizedStatus =
    normalizeStatus(status);

  return PIPELINE_STEPS.map(
    (step) => {
      if (
        step.id === "features"
      ) {
        return {
          ...step,
          state:
            normalizedStatus ===
            "parsed"
              ? "ready"
              : "ready",
        };
      }

      if (
        normalizedStatus ===
        "failed"
      ) {
        if (
          step.id ===
            "collection" ||
          step.id === "raw-email"
        ) {
          return {
            ...step,
            state: "complete",
          };
        }

        if (
          step.id === "parsing"
        ) {
          return {
            ...step,
            state: "failed",
          };
        }

        return {
          ...step,
          state: "pending",
        };
      }

      return {
        ...step,
        state: "complete",
      };
    },
  );
}

function getStateLabel(state) {
  switch (state) {
    case "complete":
      return "Complete";

    case "ready":
      return "Ready";

    case "processing":
      return "Processing";

    case "failed":
      return "Failed";

    case "pending":
    default:
      return "Pending";
  }
}

function getIndicator(state) {
  switch (state) {
    case "complete":
      return "✓";

    case "failed":
      return "!";

    case "processing":
      return "…";

    case "ready":
    case "pending":
    default:
      return "○";
  }
}

export default function PipelineStatus({
  status,
  emailId,
}) {
  const steps = getSteps(status);

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            PROCESSING PIPELINE
          </span>

          <h2>Pipeline Status</h2>

          <p>
            Processing lifecycle for this email
            across the detection platform.
          </p>
        </div>

        {emailId && (
          <code
            className="parsing-pipeline-email-id"
            title={emailId}
          >
            {emailId}
          </code>
        )}
      </header>

      <div
        className="parsing-pipeline"
        aria-label="Email processing pipeline"
      >
        {steps.map(
          (step, index) => (
            <div
              key={step.id}
              className={`parsing-pipeline-step parsing-pipeline-step--${step.state}`}
            >
              <div
                className="parsing-pipeline-step__indicator"
                aria-hidden="true"
              >
                {getIndicator(
                  step.state,
                )}
              </div>

              <div className="parsing-pipeline-step__content">
                <div className="parsing-pipeline-step__heading">
                  <div>
                    <span>
                      {step.module}
                    </span>

                    <strong>
                      {step.label}
                    </strong>
                  </div>

                  <em>
                    {getStateLabel(
                      step.state,
                    )}
                  </em>
                </div>

                <p>
                  {step.description}
                </p>
              </div>

              {index <
                steps.length - 1 && (
                <div
                  className="parsing-pipeline-step__connector"
                  aria-hidden="true"
                />
              )}
            </div>
          ),
        )}
      </div>
    </section>
  );
}