import { AlertTriangle } from "lucide-react";

/** A compact, accessible error panel shared by feature pages and forms. */
export default function ErrorNotice({ title = "Request failed", message, details = [], onRetry, className = "" }) {
  if (!message) return null;
  return <div className={`app-error-notice ${className}`} role="alert">
    <AlertTriangle size={17} aria-hidden="true" />
    <div className="app-error-notice__content">
      <strong>{title}</strong>
      <p>{message}</p>
      {details.length > 0 && <ul>{details.map((detail, index) => <li key={`${detail}-${index}`}>{detail}</li>)}</ul>}
      {onRetry && <button type="button" onClick={onRetry}>Try again</button>}
    </div>
  </div>;
}
