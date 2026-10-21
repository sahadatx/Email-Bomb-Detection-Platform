import { useCallback, useEffect, useState } from "react";
import DetectionPageShell from "../components/DetectionPageShell";
import DetectionResultsTable from "../components/DetectionResultsTable";
import { detectionService } from "../services/detectionService";
import { DETECTION_PAGE_SIZE, RISK_LEVELS } from "../types";

export default function DetectionHistoryPage() {
  const [records, setRecords] = useState([]);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState("");
  const [prediction, setPrediction] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const totalPages = Math.max(1, Math.ceil(total / DETECTION_PAGE_SIZE));
  const hasPrevious = page > 1;
  const hasNext = page < totalPages;
  const startIndex = total > 0 ? (page - 1) * DETECTION_PAGE_SIZE + 1 : 0;
  const endIndex = Math.min(page * DETECTION_PAGE_SIZE, total);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await detectionService.list({
        page,
        page_size: DETECTION_PAGE_SIZE,
        search,
        prediction,
        risk_level: riskLevel,
      });
      setRecords(response.items || []);
      setTotal(response.total || 0);
    } catch (requestError) {
      setError(requestError.message || "Could not load detection history.");
    } finally {
      setLoading(false);
    }
  }, [page, prediction, riskLevel, search]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  function updateFilter(setter, value) {
    setter(value);
    setPage(1);
  }

  function resetFilters() {
    setSearch("");
    setPrediction("");
    setRiskLevel("");
    setPage(1);
  }

  const hasFilters = Boolean(search || prediction || riskLevel);

  return (
    <DetectionPageShell
      page="history"
      title="Detection History"
      description="Search saved results and review prediction, risk, and behavioral evidence."
      loading={loading}
      error={error}
      onRefresh={loadHistory}
      selectedDetection={selected}
      onCloseDetection={() => setSelected(null)}
    >
      <section className="det-panel">
        <header>
          <div>
            <h2>Detection Records</h2>
            <p>History is sourced from persisted detection records.</p>
          </div>
          <span>{total} {total === 1 ? "record" : "records"}</span>
        </header>

        <div className="det-filters">
          <label className="det-search-field">
            <span>Search</span>
            <input
              value={search}
              onChange={(event) => updateFilter(setSearch, event.target.value)}
              placeholder="Email, sender, or detection ID"
            />
          </label>
          <label>
            <span>Prediction</span>
            <select value={prediction} onChange={(event) => updateFilter(setPrediction, event.target.value)}>
              <option value="">All predictions</option>
              <option value="bomb">Email Bomb</option>
              <option value="normal">Normal</option>
            </select>
          </label>
          <label>
            <span>Risk Level</span>
            <select value={riskLevel} onChange={(event) => updateFilter(setRiskLevel, event.target.value)}>
              <option value="">All risk levels</option>
              {RISK_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
            </select>
          </label>
        </div>
        <div className="det-filter-actions">
          <span>{hasFilters ? "Filters are applied to detection history." : "Filter detection history."}</span>
          <button className="det-secondary" type="button" disabled={!hasFilters} onClick={resetFilters}>Reset Filters</button>
        </div>

        <DetectionResultsTable
          items={records}
          onView={setSelected}
          emptyTitle={hasFilters ? "No detections match these filters" : "No detection records yet"}
          emptyDescription={hasFilters ? "Change the search or filters and try again." : "Run a detection to start building history."}
        />

        {!loading && !error && total > 0 && (
          <div className="email-pagination" aria-label="Detection history pagination">
            <div className="email-pagination-summary">
              <span>{startIndex} - {endIndex}</span>
              <span>/ Total {total}</span>
            </div>

            <div className="email-pagination-controls">
              <button
                type="button"
                className="email-pagination-button"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={!hasPrevious || loading}
                aria-label="Go to previous page"
              >
                <span aria-hidden="true">‹</span>
                Previous
              </button>

              <span className="email-pagination-page">
                Page <strong>{page}</strong> of <strong>{totalPages}</strong>
              </span>

              <button
                type="button"
                className="email-pagination-button"
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={!hasNext || loading}
                aria-label="Go to next page"
              >
                Next
                <span aria-hidden="true">›</span>
              </button>
            </div>
          </div>
        )}

        {!loading && !error && total === 0 && (
          <div className="email-pagination email-pagination-empty">
            <span>No detection records available.</span>
          </div>
        )}
      </section>
    </DetectionPageShell>
  );
}
