export default function LoadingState({ children = "Loading records…" }) {
  return <div className="ir-state" role="status" aria-live="polite"><span className="ir-spinner" aria-hidden="true"/>{children}</div>;
}
