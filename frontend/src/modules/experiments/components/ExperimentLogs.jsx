import { formatDate } from "../types";

export default function ExperimentLogs({ items = [] }) {
  if (!items.length) return <div className="ex-empty">No log entries returned.</div>;
  return <ol className="ex-logs">{items.map((entry, index) => <li key={`${entry.timestamp || "log"}-${index}`}><time>{formatDate(entry.timestamp)}</time><span>{entry.message}</span></li>)}</ol>;
}
