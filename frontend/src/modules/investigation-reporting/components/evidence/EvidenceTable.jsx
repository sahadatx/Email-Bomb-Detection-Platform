import { useState } from "react";
import { Eye, Pencil, ShieldCheck } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import ActionMenu from "../common/ActionMenu";

const dateTime = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return { date: date.toLocaleDateString(), time: date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) };
};
const ALL_COLUMNS = [
  ["evidence", "Evidence"],
  ["type", "Type"],
  ["detection", "Detection"],
  ["source", "Source Email"],
  ["collected", "Collected"],
  ["status", "Status"],
];

export default function EvidenceTable({ items = [], canManage, onView, onEdit, onReview, onDetection, onAudit }) {
  const [columns, setColumns] = useState(["evidence", "type", "detection", "collected", "status"]);
  const toggle = (key) => setColumns((current) => current.includes(key) ? current.filter((item) => item !== key) : [...current, key]);
  const cell = (item, key) => {
    if (key === "evidence") return <><button className="ir-link-button" onClick={() => onView(item)}>{item.name}</button><small className="ir-evidence-id" title={String(item.id)}>{String(item.id)}</small></>;
    if (key === "type") return item.evidence_type?.replaceAll("_", " ");
    if (key === "detection") return <button className="ir-link-button ir-evidence-id" title={String(item.detection_id)} onClick={() => onDetection(item)}>{String(item.detection_id)}</button>;
    if (key === "source") return item.source_email_id ? `${String(item.source_email_id).slice(0, 13)}…` : "—";
    if (key === "collected") { const collected = dateTime(item.collected_at || item.created_at); return collected ? <span className="ir-evidence-collected"><span>{collected.date}</span><span>{collected.time}</span></span> : "—"; }
    if (key === "status") return <StatusBadge status={item.review_status}/>;
    return "—";
  };

  return <>
    <div className="ir-table-tools"><details className="ir-column-picker"><summary>Columns</summary><div>{ALL_COLUMNS.map(([key, label]) => <label key={key}><input type="checkbox" checked={columns.includes(key)} onChange={() => toggle(key)}/>{label}</label>)}</div></details></div>
    <div className="ir-table-wrap"><table className="ir-table"><thead><tr>{ALL_COLUMNS.filter(([key]) => columns.includes(key)).map(([key, label]) => <th key={key}>{label}</th>)}<th>Actions</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}>{ALL_COLUMNS.filter(([key]) => columns.includes(key)).map(([key]) => <td key={key}>{cell(item, key)}</td>)}<td><ActionMenu label="Evidence actions" items={[
      { label: "View details", icon: Eye, onClick: () => onView(item) },
      { label: "Edit evidence", icon: Pencil, disabled: !canManage, onClick: () => onEdit(item) },
      { label: "Change review status", icon: ShieldCheck, disabled: !canManage, onClick: () => onReview(item) },
      ...(onAudit ? [{ label: "View audit history", icon: Eye, onClick: () => onAudit(item) }] : []),
    ]}/></td></tr>)}</tbody></table></div>
  </>;
}
