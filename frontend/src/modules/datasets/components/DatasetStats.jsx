
import React from "react";
import { Database, Mail, ShieldAlert } from "lucide-react";

const STAT_CONFIG = [
  {
    key: "total_emails",
    label: "Dataset Emails",
    description: "Feature-extracted samples",
    Icon: Database,
    accent: "blue",
  },
  {
    key: "normal_count",
    label: "Normal",
    description: "Ground-truth normal samples",
    Icon: Mail,
    accent: "green",
  },
  {
    key: "bombing_count",
    label: "Bombing",
    description: "Ground-truth bombing samples",
    Icon: ShieldAlert,
    accent: "red",
  },
];

function formatCount(value) {
  const count = Number(value);

  if (!Number.isFinite(count) || count < 0) {
    return "—";
  }

  return new Intl.NumberFormat().format(count);
}

export default function DatasetStats({
  summary,
  loading = false,
  className = "",
}) {
  return (
    <section
      className={`dataset-stats ${className}`.trim()}
      aria-label="Dataset summary"
    >
      {STAT_CONFIG.map(({ key, label, description, Icon, accent }) => (
        <article
          className={`dataset-stat-card dataset-stat-card--${accent}`}
          key={key}
        >
          <div className="dataset-stat-card__top">
            <div className="dataset-stat-card__heading">
              <h2 className="dataset-stat-card__label">{label}</h2>
              <p className="dataset-stat-card__description">
                {description}
              </p>
            </div>

            <div className="dataset-stat-card__icon" aria-hidden="true">
              <Icon size={21} strokeWidth={1.8} />
            </div>
          </div>

          <div
            className="dataset-stat-card__value"
            aria-live="polite"
            aria-busy={loading}
          >
            {loading ? (
              <span
                className="dataset-skeleton dataset-skeleton--stat"
                aria-label={`Loading ${label}`}
              />
            ) : (
              formatCount(summary?.[key])
            )}
          </div>
        </article>
      ))}
    </section>
  );
}