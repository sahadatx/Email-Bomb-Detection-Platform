import { Link } from "react-router-dom";
import DetailsDrawer from "../common/DetailsDrawer";
import DetectionSummary from "./DetectionSummary";
import ModelInformation from "./ModelInformation";
import FeatureContributionChart from "./FeatureContributionChart";
import TriggeredRuleList from "./TriggeredRuleList";
import RiskBreakdown from "./RiskBreakdown";
import BehavioralSignals from "./BehavioralSignals";
import AnalystNoteList from "./AnalystNoteList";
export default function ExplanationDetailsDrawer({ open, detection, loading, error, onClose, notes, userId, isAdmin, canAddNote, canExport, onAddNote, onEditNote, onDeleteNote }) {
  return <DetailsDrawer open={open} title="Explanation Details" description={detection?.id ? `Detection ${detection.id}` : "Persisted detection and model explanation"} onClose={onClose} loading={loading} error={error} footer={detection?.id && <><Link className="ir-button ir-button--secondary" to={`/detection/history?detection_id=${detection.id}`}>View Detection</Link><Link className="ir-button ir-button--secondary" to={`/evidence?detection_id=${detection.id}`}>View Evidence</Link><Link className="ir-button ir-button--secondary" to={`/reports?detection_id=${detection.id}`}>View Reports</Link>{canAddNote && <button className="ir-button ir-button--secondary" onClick={onAddNote}>Add Note</button>}{canExport && <button className="ir-button ir-button--primary" onClick={onExport}>Export JSON</button>}</>}>
    {detection?.id && <div className="ir-detail-stack"><DetectionSummary detection={detection}/><ModelInformation detection={detection}/><FeatureContributionChart explanation={detection.explanation}/><TriggeredRuleList rules={detection.explanation?.triggered_rules || detection.risk?.factors || []}/><RiskBreakdown risk={detection.risk}/><BehavioralSignals behavioral={detection.behavioral}/><AnalystNoteList notes={notes || detection.analyst_notes || []} userId={userId} isAdmin={isAdmin} canManageNotes={canAddNote} onEdit={onEditNote} onDelete={onDeleteNote}/></div>}
  </DetailsDrawer>;
}
