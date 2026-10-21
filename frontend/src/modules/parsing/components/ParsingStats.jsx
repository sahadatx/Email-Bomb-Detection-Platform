// ============================================================================
// Email Parsing & Normalization
// Module 03
// ============================================================================
//
// Displays the global parsing state of Module 03.
//
// IMPORTANT:
// These values represent the complete parsing state across all
// collected emails, not only the currently visible pagination page.
//
// Global statistics:
//
//   - Collected
//   - Parsed
//   - Pending
//   - Warnings
//   - Failed
//
// Selection count is intentionally NOT displayed here because selection
// is a temporary UI/action state rather than a global parsing statistic.
//
// FEATURE READY is intentionally NOT displayed here.
// Feature readiness belongs to Module 04 Feature Engineering.
// ============================================================================



// ============================================================================
// Statistic Configuration
// ============================================================================

const STAT_CONFIG = Object.freeze([
  {
    key: "total_collected",
    label: "COLLECTED",
  },

  {
    key: "total_parsed",
    label: "PARSED",
  },

  {
    key: "total_pending",
    label: "PENDING",
  },

  {
    key: "total_warnings",
    label: "WARNINGS",
  },

  {
    key: "total_failed",
    label: "FAILED",
  },
]);



// ============================================================================
// Helpers
// ============================================================================

function normalizeCount(value) {
  const number = Number(value);

  if (
    !Number.isFinite(number) ||
    number < 0
  ) {
    return 0;
  }

  return Math.floor(number);
}



// ============================================================================
// Component
// ============================================================================

export default function ParsingStats({
  totalCollected = 0,
  totalParsed = 0,
  totalPending = 0,
  totalWarnings = 0,
  totalFailed = 0,
}) {
  const values = {
    total_collected:
      normalizeCount(
        totalCollected,
      ),

    total_parsed:
      normalizeCount(
        totalParsed,
      ),

    total_pending:
      normalizeCount(
        totalPending,
      ),

    total_warnings:
      normalizeCount(
        totalWarnings,
      ),

    total_failed:
      normalizeCount(
        totalFailed,
      ),
  };

  return (
    <section
      className="parsing-stats"
      aria-label="Global parsing statistics"
    >
      {STAT_CONFIG.map(
        (stat) => (
          <article
            key={stat.key}
            className={
              `parsing-stat-card parsing-stat-card--${stat.key}`
            }
          >
            <span className="parsing-stat-card__label">
              {stat.label}
            </span>

            <strong className="parsing-stat-card__value">
              {values[stat.key]}
            </strong>
          </article>
        ),
      )}
    </section>
  );
}