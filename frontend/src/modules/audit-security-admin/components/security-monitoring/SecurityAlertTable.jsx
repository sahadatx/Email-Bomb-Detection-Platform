import { Eye, ShieldCheck } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import { displayDate } from "../../types";

export default function SecurityAlertTable({ items = [], canInvestigate, onView, onInvestigate }) {
  return <div className="asa-table-scroll"><table className="asa-table"><thead><tr><th>Alert</th><th>Severity</th><th>Status</th><th>Events</th><th>First / Last Seen</th><th>Assigned To</th><th>Action</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><strong>{item.title}</strong><small>{String(item.id).slice(0, 14)} · Rule {item.rule_id ? String(item.rule_id).slice(0, 10) : "—"}</small></td><td><StatusBadge status={item.severity}/></td><td><StatusBadge status={item.status}/></td><td>{item.event_count}</td><td>{displayDate(item.first_seen)}<small>Last: {displayDate(item.last_seen)}</small></td><td>{item.assignee_name || "Unassigned"}</td><td className="asa-inline-actions"><button className="asa-row-button asa-row-button--view" onClick={() => onView(item)}><Eye size={14}/> View</button>{canInvestigate && item.status !== "resolved" && <button className="asa-row-button asa-row-button--investigate" onClick={() => onInvestigate(item)}><ShieldCheck size={14}/> Investigate</button>}</td></tr>)}</tbody></table></div>;
}
