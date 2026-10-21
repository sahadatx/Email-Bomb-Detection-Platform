import { useState } from "react";
import { Link } from "react-router-dom";
import { Eye, RefreshCw } from "lucide-react";
import ThreatPageHeader from "../components/ThreatPageHeader";
import ThreatSummaryCards from "../components/ThreatSummaryCards";
import ThreatActivityTrends from "../components/ThreatActivityTrends";
import ThreatTypeDistribution from "../components/ThreatTypeDistribution";
import ThreatSeverityDistribution from "../components/ThreatSeverityDistribution";
import ThreatDrawer from "../components/ThreatDrawer";
import ThreatMatchDetails from "../components/ThreatMatchDetails";
import ThreatRelatedRecord from "../components/ThreatRelatedRecord";
import { apiRequest } from "../../../core/api/client";
import useThreatOverview from "../hooks/useThreatOverview";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import {
  errorMessage,
  displayDate,
  displayLabel,
} from "../types/threatIntelligence";
import "../styles/threatIntelligence.css";

const DEFAULTS = {
  time_range: "30d",
  from_date: "",
  to_date: "",
  threat_type: "",
  severity: "",
  feed_id: "",
};
export default function ThreatOverviewPage() {
  const { data, loading, error, refresh } = useThreatOverview(DEFAULTS);
  const [selected, setSelected] = useState(null);
  const [relatedRecord, setRelatedRecord] = useState(null);
  const [relatedStack, setRelatedStack] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);
  const [relatedError, setRelatedError] = useState("");
  async function openRelated(kind, id) {
    if (!id || !selected) return;
    setRelatedStack((stack) => [...stack, relatedRecord]);
    setRelatedLoading(true);
    setRelatedError("");
    try {
      const path =
        kind === "email"
          ? `/emails/${encodeURIComponent(id)}`
          : kind === "detection"
            ? `/detection/${encodeURIComponent(id)}`
            : null;
      const result =
        kind === "indicator"
          ? await threatIntelligenceService.indicator(id)
          : await apiRequest(path);
      setRelatedRecord({ kind, data: result });
    } catch (cause) {
      setRelatedError(errorMessage(cause));
      setRelatedRecord({ kind, data: null });
    } finally {
      setRelatedLoading(false);
    }
  }
  function backToPreviousRecord() {
    setRelatedRecord(relatedStack.at(-1) || null);
    setRelatedStack((stack) => stack.slice(0, -1));
  }
  return (
    <main className="ti-page">
      <ThreatPageHeader
        title="Threat Overview"
        description="Monitor threat intelligence and emerging threats"
      >
        <button
          className="ti-button ti-button--secondary"
          disabled={loading}
          onClick={refresh}
        >
          <RefreshCw size={15} /> Refresh
        </button>
      </ThreatPageHeader>
      {error ? (
        <div className="ti-state ti-error" role="alert">
          <strong>Threat overview could not be loaded.</strong>
          <span>{error}</span>
          <button className="ti-button ti-button--secondary" onClick={refresh}>
            Retry
          </button>
        </div>
      ) : (
        <>
          <ThreatSummaryCards
            loading={loading}
            items={
              data
                ? [
                    {
                      label: "Total Indicators",
                      value: data.total_indicators,
                      caption: "Active indicators",
                    },
                    {
                      label: "Active Feeds",
                      value: data.active_feeds,
                      caption: "Enabled sources",
                    },
                    {
                      label: "Threat Matches",
                      value: data.threat_matches,
                      caption: "In the last 30 days",
                    },
                    {
                      label: "Critical Threats",
                      value: data.critical_threats,
                      caption: "Critical matches",
                    },
                  ]
                : [
                    "Total Indicators",
                    "Active Feeds",
                    "Threat Matches",
                    "Critical Threats",
                  ].map((label) => ({ label, value: 0, caption: "" }))
            }
          />
          <div className="ti-content-grid ti-content-grid--wide">
            <ThreatActivityTrends items={data?.trends || []} />
            <ThreatTypeDistribution items={data?.types || []} />
            <ThreatSeverityDistribution items={data?.severities || []} />
          </div>
          <section className="ti-panel">
            <header>
              <div>
                <h2>Recent Threat Matches</h2>
                <p>
                  Persisted email-to-indicator matches from the last 30 days
                </p>
              </div>
              <Link
                to="/threat-intelligence/matches"
                className="ti-text-button"
              >
                View all →
              </Link>
            </header>
            <div className="ti-table-wrap">
              <table className="ti-table">
                <thead>
                  <tr>
                    <th>Indicator</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Email</th>
                    <th>Matched</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {(data?.recent_matches || []).map((match) => (
                    <tr
                      key={match.id}
                      onClick={() => {
                        setSelected(match);
                        setRelatedRecord(null);
                        setRelatedStack([]);
                        setRelatedError("");
                      }}
                    >
                      <td className="ti-indicator-value">
                        {match.indicator_value}
                      </td>
                      <td>{match.indicator_type}</td>
                      <td>
                        <span
                          className={`ti-severity ti-severity--${match.severity}`}
                        >
                          {match.severity}
                        </span>
                      </td>
                      <td>{match.email_label || match.email_id}</td>
                      <td>{displayDate(match.matched_at)}</td>
                      <td>
                        <button className="ti-text-button">
                          <Eye size={14} aria-hidden="true" /> View →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!data?.recent_matches?.length && (
                <div className="ti-empty">
                  No threat matches in this period.
                </div>
              )}
            </div>
          </section>
        </>
      )}
      <ThreatDrawer
        open={Boolean(selected)}
        title={
          relatedRecord
            ? `${displayLabel(relatedRecord.kind)} Details`
            : "Threat Match Details"
        }
        subtitle={relatedRecord?.data?.id || selected?.indicator_value}
        back={relatedStack.length ? backToPreviousRecord : undefined}
        onClose={() => {
          setSelected(null);
          setRelatedRecord(null);
          setRelatedStack([]);
        }}
      >
        {relatedLoading ? (
          <div className="ti-empty">Loading related record…</div>
        ) : relatedRecord ? (
          <ThreatRelatedRecord
            kind={relatedRecord.kind}
            data={relatedRecord.data}
          />
        ) : (
          <ThreatMatchDetails match={selected} onRelated={openRelated} />
        )}
        {relatedError && <div className="ti-form-error">{relatedError}</div>}
      </ThreatDrawer>
    </main>
  );
}
