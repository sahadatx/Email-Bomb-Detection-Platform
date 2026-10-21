const DEFAULT_STATS = {
  total_emails: 0,
  normal_emails: 0,
  bombing_emails: 0,
};


function StatCard({
  label,
  value,
  description,
  icon,
}) {
  return (
    <article className="email-stat-card">
      <div className="email-stat-card-header">
        <span className="email-stat-card-label">
          {label}
        </span>

        <span
          className="email-stat-card-icon"
          aria-hidden="true"
        >
          {icon}
        </span>
      </div>

      <div className="email-stat-card-value">
        {value}
      </div>

      <div className="email-stat-card-description">
        {description}
      </div>
    </article>
  );
}


export default function EmailStats({
  stats = DEFAULT_STATS,
}) {
  const safeStats = {
    ...DEFAULT_STATS,
    ...(stats || {}),
  };

  return (
    <section
      className="email-stats-grid"
      aria-label="Email management statistics"
    >
      <StatCard
        label="Total Emails"
        value={safeStats.total_emails}
        description="Emails stored in the platform"
        icon="✉"
      />

      <StatCard
        label="Normal"
        value={safeStats.normal_emails}
        description="Emails labeled as normal"
        icon="✓"
      />

      <StatCard
        label="Bombing"
        value={safeStats.bombing_emails}
        description="Emails labeled as bombing"
        icon="!"
      />
    </section>
  );
}