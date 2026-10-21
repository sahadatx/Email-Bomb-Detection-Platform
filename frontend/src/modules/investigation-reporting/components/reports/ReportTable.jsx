import { Archive, Copy, Download, Eye, FilePenLine, Play, ScanEye } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import ActionMenu from "../common/ActionMenu";

const dt = (value) => value ? new Date(value).toLocaleString() : "—";

export default function ReportTable({ items = [], canManage, canEditDraft, canArchive, onView, onPreview, onEdit, onGenerate, onDownload, onDuplicate, onArchive }) {
  return <div className="ir-table-wrap"><table className="ir-table"><thead><tr><th>Report</th><th>Type</th><th>Format</th><th>Detections</th><th>Status</th><th>Updated</th><th>Actions</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}>
    <td><button className="ir-link-button" onClick={() => onView(item)}>{item.title}</button><small className="ir-report-id" title={String(item.id)}>{String(item.id)}</small></td>
    <td>{item.report_type}</td><td>{item.output_format?.toUpperCase()}</td><td>{item.detection_ids?.length || 0}</td><td><StatusBadge status={item.status}/></td><td>{dt(item.updated_at)}</td>
    <td><ActionMenu label="Report actions" items={[
      { label: "View details", icon: Eye, onClick: () => onView(item) },
      ...(item.status === "generated" ? [{ label: "Preview report", icon: ScanEye, onClick: () => onPreview(item) }] : []),
      ...(canEditDraft && item.status === "draft" ? [{ label: "Edit draft", icon: FilePenLine, onClick: () => onEdit(item) }] : []),
      ...(canManage && ["draft", "failed"].includes(item.status) ? [{ label: "Generate / retry", icon: Play, onClick: () => onGenerate(item) }] : []),
      ...(item.status === "generated" ? [{ label: "Download", icon: Download, onClick: () => onDownload(item) }] : []),
      ...(canManage ? [{ label: "Duplicate", icon: Copy, onClick: () => onDuplicate(item) }] : []),
      ...(canArchive && item.status !== "archived" ? [{ label: "Archive", icon: Archive, danger: true, onClick: () => onArchive(item) }] : []),
    ]}/></td>
  </tr>)}</tbody></table></div>;
}
