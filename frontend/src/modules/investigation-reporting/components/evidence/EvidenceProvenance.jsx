export default function EvidenceProvenance({ evidence }) {
  return <section className="ir-detail-card"><h3>Evidence Value & Provenance</h3><pre className="ir-pre">{evidence.observed_value || "No observed value supplied."}</pre><dl className="ir-dl"><dt>Source</dt><dd>{evidence.provenance?.source || "Not recorded"}</dd><dt>Metadata</dt><dd><pre className="ir-pre">{JSON.stringify(evidence.provenance || {}, null, 2)}</pre></dd><dt>Analyst Note</dt><dd>{evidence.analyst_note || "—"}</dd></dl></section>;
}
