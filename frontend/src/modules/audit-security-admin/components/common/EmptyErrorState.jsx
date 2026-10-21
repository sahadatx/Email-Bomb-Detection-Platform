import { AlertCircle, Inbox } from "lucide-react";

export function EmptyState({ title = "No records found", description = "Try changing the filters or search terms." }) { return <div className="asa-state"><Inbox size={25}/><strong>{title}</strong><span>{description}</span></div>; }
export function ErrorState({ error, onRetry }) { return <div className="asa-state asa-state--error"><AlertCircle size={25}/><strong>Could not load this information</strong><span>{error}</span><button className="asa-button asa-button--secondary" onClick={onRetry}>Try again</button></div>; }
