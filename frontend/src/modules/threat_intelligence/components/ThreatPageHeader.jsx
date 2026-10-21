export default function ThreatPageHeader({
  eyebrow = "THREAT INTELLIGENCE",
  title,
  description,
  children,
}) {
  return (
    <header className="ti-page-head">
      <div>
        <span className="ti-eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children && <div className="ti-page-actions">{children}</div>}
    </header>
  );
}
