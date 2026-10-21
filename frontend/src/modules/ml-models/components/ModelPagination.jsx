import React from "react";

export default function ModelPagination({ page, pageSize, total, loading, onPage }) {
  if (loading) return null;
  if (!total) {
    return (
      <div className="ml-pagination ml-pagination--empty" aria-live="polite">
        <span>No records available.</span>
      </div>
    );
  }
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <nav className="ml-pagination" aria-label="Pagination">
      <div className="ml-pagination__summary">
        <span>{start} - {end}</span>
        <span>/ Total {total}</span>
      </div>
      <div className="ml-pagination__controls">
        <button type="button" onClick={() => onPage(page - 1)} disabled={page <= 1} aria-label="Go to previous page">
          <span aria-hidden="true">‹</span> Previous
        </button>
        <span className="ml-pagination__page">Page <strong>{page}</strong> of <strong>{totalPages}</strong></span>
        <button type="button" onClick={() => onPage(page + 1)} disabled={page >= totalPages} aria-label="Go to next page">
          Next <span aria-hidden="true">›</span>
        </button>
      </div>
    </nav>
  );
}
