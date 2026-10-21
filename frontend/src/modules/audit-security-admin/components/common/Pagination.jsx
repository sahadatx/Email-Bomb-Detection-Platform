export default function Pagination({ page = 1, pageSize = 30, total = 0, onPage, className = "" }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const start = total ? (page - 1) * pageSize + 1 : 0;
  const end = Math.min(page * pageSize, total);
  return <div className={`asa-pagination ${className}`.trim()} aria-label="Pagination"><span className="asa-pagination-summary"><strong>{start} - {end}</strong><span>/ Total {total.toLocaleString()}</span></span><div className="asa-pagination-controls"><button type="button" aria-label="Go to previous page" disabled={page <= 1} onClick={() => onPage(page - 1)}><span aria-hidden="true">‹</span>Previous</button><span className="asa-pagination-page">Page <strong>{page}</strong> of <strong>{pages}</strong></span><button type="button" aria-label="Go to next page" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next<span aria-hidden="true">›</span></button></div></div>;
}
