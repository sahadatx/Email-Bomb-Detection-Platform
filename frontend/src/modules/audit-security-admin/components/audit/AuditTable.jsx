import { ArrowDown, ArrowUp, Eye } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import { displayDate } from "../../types";

const columns = [["created_at", "Timestamp"], ["actor_name", "Actor"], ["action", "Action / Target"], ["status", "Status"], ["severity", "Severity"], ["source", "Source"]];
export default function AuditTable({ items = [], sortBy, sortOrder, onSort, onView }) {
  return <div className="asa-table-scroll"><table className="asa-table"><thead><tr>{columns.map(([key, label]) => <th key={key}><button className="asa-sort" onClick={() => onSort(key)}>{label}{sortBy === key && (sortOrder === "asc" ? <ArrowUp size={12}/> : <ArrowDown size={12}/>)}</button></th>)}<th>IP Address</th><th>Details</th></tr></thead><tbody>{items.map((event) => <tr key={event.id}><td>{displayDate(event.created_at)}</td><td><strong>{event.actor_name || "System"}</strong><small>{event.actor_role || "Service"}</small></td><td><strong>{event.action}</strong><small>{event.target_label || event.target_type || event.target_id || "—"}</small></td><td><StatusBadge status={event.status}/></td><td>{event.severity ? <StatusBadge status={event.severity}/> : "—"}</td><td>{event.source}</td><td>{event.ip_address || "—"}</td><td><button className="asa-row-button asa-row-button--view" onClick={() => onView(event)}><Eye size={14}/> View</button></td></tr>)}</tbody></table></div>;
}
