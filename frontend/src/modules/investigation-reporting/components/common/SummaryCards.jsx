export default function SummaryCards({ items = [], loading = false }) {
  return <section className="ir-kpi-grid" aria-label="Summary">{items.map(({ label, value }, index) => <article className={`ir-kpi ir-kpi--${index % 4}`} key={label}><span>{label}</span><strong>{loading ? "…" : value == null ? "—" : Number(value).toLocaleString()}<i aria-hidden="true"/></strong></article>)}</section>;
}
