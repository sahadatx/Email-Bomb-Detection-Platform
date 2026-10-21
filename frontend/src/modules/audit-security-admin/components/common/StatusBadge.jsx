export default function StatusBadge({ status }) {
  const value = String(status || "unknown").toLowerCase();
  return <span className={`asa-status asa-status--${value.replaceAll("_", "-")}`}>{value.replaceAll("_", " ")}</span>;
}
