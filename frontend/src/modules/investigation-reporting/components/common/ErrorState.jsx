export default function ErrorState({ message, onRetry }) {
  return <div className="ir-state ir-state--error" role="alert"><strong>Could not load records</strong><span>{message || "The request failed."}</span>{onRetry && <button className="ir-button ir-button--secondary" type="button" onClick={onRetry}>Try again</button>}</div>;
}
