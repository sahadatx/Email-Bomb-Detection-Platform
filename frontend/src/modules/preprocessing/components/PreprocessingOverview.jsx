import {
  Database,
  Play,
  CheckCircle2,
  XCircle,
  Info,
} from "lucide-react";

const OVERVIEW_ITEMS = [
  {
    id: "datasets",
    label: "Available Datasets",
    key: "available_datasets",
    icon: Database,
    color: "blue",
  },
  {
    id: "runs",
    label: "Total Runs",
    key: "total_runs",
    icon: Play,
    color: "violet",
  },
  {
    id: "successful",
    label: "Successful Runs",
    key: "successful_runs",
    icon: CheckCircle2,
    color: "green",
  },
  {
    id: "failed",
    label: "Failed Runs",
    key: "failed_runs",
    icon: XCircle,
    color: "red",
  },
];

function formatCount(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const count = Number(value);

  if (!Number.isFinite(count) || count < 0) {
    return "—";
  }

  return count.toLocaleString();
}

export default function PreprocessingOverview({
  stats = null,
  loading = false,
  error = "",
}) {
  const hasStats =
    stats !== null &&
    typeof stats === "object" &&
    !Array.isArray(stats);

  return (
    <section
      className="preprocessing-overview"
      aria-labelledby="preprocessing-overview-title"
    >
      <div className="preprocessing-section-heading">
        <div>
          <h2 id="preprocessing-overview-title">
            Overview
          </h2>
          <p>Dataset and preprocessing run summary</p>
        </div>

        <span className="preprocessing-mock-badge">
          <Info size={14} aria-hidden="true" />
          {loading
            ? "Loading"
            : hasStats
              ? "Backend data"
              : "No data"}
        </span>
      </div>

      {error && (
        <div
          className="preprocessing-validation-error"
          role="alert"
        >
          <Info size={16} aria-hidden="true" />
          <p>{error}</p>
        </div>
      )}

      <div className="preprocessing-overview-grid">
        {OVERVIEW_ITEMS.map((item) => {
          const Icon = item.icon;
          const value = hasStats ? stats[item.key] : null;

          return (
            <article
              key={item.id}
              className={`preprocessing-stat-card preprocessing-stat-${item.color}`}
            >
              <div className="preprocessing-stat-card-top">
                <div className="preprocessing-stat-icon">
                  <Icon size={20} aria-hidden="true" />
                </div>

              </div>

              <div className="preprocessing-stat-content">
                <p className="preprocessing-stat-label">
                  {item.label}
                </p>

                <p className="preprocessing-stat-value">
                  {loading ? "…" : formatCount(value)}
                </p>

                <p className="preprocessing-stat-description">
                  {hasStats
                    ? "From your workspace"
                    : "Waiting for backend data"}
                </p>
              </div>
            </article>
          );
        })}
      </div>

      {!hasStats && !loading && !error && (
        <div className="preprocessing-overview-notice">
          <Info size={16} aria-hidden="true" />
          <p>
            Overview statistics are not available yet.
            Values will appear when the backend provides them.
          </p>
        </div>
      )}
    </section>
  );
}
