import { Activity, AlertTriangle } from "lucide-react";
import { formatCount } from "../types";

export default function BehavioralAnalytics({ data }) {
  const max = Math.max(1, ...(data?.activity || []).map((row) => row.emails));
  return <section className="an-panel"><header className="an-panel-heading"><div><h2>Behavioral Analytics</h2><p>Stored behavior results associated with completed detections</p></div></header>{data?.available ? <><div className="an-behavior-cards"><article><Activity size={17}/><span>Burst Events</span><strong>{formatCount(data.burst_events)}</strong></article><article><AlertTriangle size={17}/><span>Suspicious Patterns</span><strong>{formatCount(data.suspicious_patterns)}</strong></article></div><div className="an-hourly-bars">{data.activity.map((row) => <div key={row.timestamp} title={`${row.timestamp}: ${row.emails} analysis results`}><i style={{ height: `${Math.max(4, row.emails / max * 100)}%` }}/><small>{new Date(row.timestamp).toLocaleTimeString(undefined, { hour: "numeric" })}</small></div>)}</div></> : <div className="an-empty">Behavioral analysis is unavailable for the selected records.</div>}</section>;
}
