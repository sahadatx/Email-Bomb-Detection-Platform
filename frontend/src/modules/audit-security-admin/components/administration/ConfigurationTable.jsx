import { Pencil } from "lucide-react";
import { displayDate } from "../../types";

export default function ConfigurationTable({ items = [], canEdit, onEdit }) {
  return <div className="asa-table-scroll"><table className="asa-table"><thead><tr><th>Setting</th><th>Category</th><th>Value</th><th>Updated By</th><th>Updated At</th><th>Action</th></tr></thead><tbody>{items.map((item) => <tr key={item.key}><td><strong>{item.key}</strong></td><td>{item.category.replaceAll("_", " ")}</td><td>{item.secret ? "••••••••" : String(item.value)}</td><td>{item.updated_by || "—"}</td><td>{displayDate(item.updated_at)}</td><td><button className="asa-row-button asa-row-button--edit" disabled={!canEdit || item.secret} onClick={() => onEdit(item)}><Pencil size={14}/> Edit</button></td></tr>)}</tbody></table></div>;
}
