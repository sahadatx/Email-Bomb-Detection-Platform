export default function EvidenceRelationships({ evidence }) {
  return <section className="ir-detail-card"><h3>Related Records</h3><dl className="ir-dl"><dt>Detection ID</dt><dd>{evidence.detection_id}</dd><dt>Source Email ID</dt><dd>{evidence.source_email_id || "Not linked"}</dd></dl></section>;
}
