import ConfirmDialog from "../common/ConfirmDialog";
export default function ReportGenerationDialog({ open, report, busy, onCancel, onConfirm }) {
  return <ConfirmDialog open={open} title="Generate this report?" message={`The backend will capture the selected detections and requested sections into an immutable snapshot for “${report?.title || "this report"}”.`} confirmLabel="Generate Report" busy={busy} onCancel={onCancel} onConfirm={onConfirm}/>;
}
