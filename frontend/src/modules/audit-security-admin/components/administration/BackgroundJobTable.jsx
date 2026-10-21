import { Eye } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import { displayDate } from "../../types";

export default function BackgroundJobTable({ items = [], onView }) {
  return <div className="asa-table-scroll"><table className="asa-table"><thead><tr><th>Job ID</th><th>Type</th><th>Status</th><th>Progress</th><th>Related Resource</th><th>Started At</th><th>Action</th></tr></thead><tbody>{items.map((job) => <tr key={`${job.job_type}-${job.id}`}><td><code>{String(job.id).slice(0, 16)}</code></td><td>{job.job_type.replaceAll("_", " ")}</td><td><StatusBadge status={job.status}/></td><td>{job.progress == null ? "—" : `${job.progress}%`}</td><td>{job.related_resource || "—"}</td><td>{displayDate(job.started_at)}</td><td><button type="button" className="asa-row-button asa-row-button--view" onClick={() => onView(job)} aria-label={`View background job ${job.id}`}><Eye size={15} aria-hidden="true"/> View</button></td></tr>)}</tbody></table></div>;
}
