import ErrorNotice from "../../../core/components/ErrorNotice";

export default function SettingsErrorState({ error, onRetry }) {
  return <div className="settings-error-state"><ErrorNotice title="Settings could not be loaded" message={error} onRetry={onRetry} /></div>;
}
