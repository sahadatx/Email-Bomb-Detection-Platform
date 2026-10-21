export default function StatusBadge({ status }) {
  const value = String(status || "unavailable").toLowerCase();
  return <span className={`ir-status ir-status--${value}`}>{value.replaceAll("_", " ")}</span>;
}
