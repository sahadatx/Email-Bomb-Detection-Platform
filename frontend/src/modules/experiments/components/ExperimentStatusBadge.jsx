import { statusLabel } from "../types";

export default function ExperimentStatusBadge({ status }) {
  return <span className={`ex-status ex-status--${status || "draft"}`}><i/>{statusLabel(status)}</span>;
}
