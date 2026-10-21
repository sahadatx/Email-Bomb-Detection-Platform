export default function EmptyState({ title, description, action, noResults = false }) {
  return <div className="ir-state"><strong>{title}</strong><span>{description}</span>{noResults && <small>Clear one or more filters to broaden the results.</small>}{action}</div>;
}
