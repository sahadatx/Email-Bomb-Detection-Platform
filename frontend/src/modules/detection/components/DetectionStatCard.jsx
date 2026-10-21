export default function DetectionStatCard({ icon: Icon, label, value, tone = "blue", detail }) {
  return (
    <article className="det-stat">
      <span className={`det-stat-icon ${tone}`} aria-hidden="true">
        <Icon size={18} />
      </span>
      <div>
        <small>{label}</small>
        <strong>{value ?? "—"}</strong>
        {detail && <span className="det-stat-detail">{detail}</span>}
      </div>
    </article>
  );
}
