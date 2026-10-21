export default function Pagination({ page, pageSize, total, onPage, loading = false, error = false }) {
  const count = Number(total || 0);
  const pages = Math.max(1, Math.ceil(count / pageSize));
  const start = count ? (page - 1) * pageSize + 1 : 0;
  const end = Math.min(page * pageSize, count);

  if (loading || error) return null;

  if (!count) {
    return (
      <nav className="email-pagination email-pagination-empty" aria-label="Pagination">
        <span>No records available.</span>
      </nav>
    );
  }

  return (
    <nav className="email-pagination" aria-label="Pagination">
      <div className="email-pagination-summary">
        <span>{start} - {end}</span>
        <span>/ Total {count.toLocaleString()}</span>
      </div>

      <div className="email-pagination-controls">
        <button type="button" className="email-pagination-button" onClick={() => onPage(Math.max(1, page - 1))} disabled={page <= 1 || loading} aria-label="Go to previous page">
          <span aria-hidden="true">‹</span> Previous
        </button>
        <span className="email-pagination-page">Page <strong>{page}</strong> of <strong>{pages}</strong></span>
        <button type="button" className="email-pagination-button" onClick={() => onPage(Math.min(pages, page + 1))} disabled={page >= pages || loading} aria-label="Go to next page">
          Next <span aria-hidden="true">›</span>
        </button>
      </div>
    </nav>
  );
}
