import { useCallback, useEffect, useState } from "react";
import { Save, Settings2, ShieldCheck } from "lucide-react";
import DetectionPageShell from "../components/DetectionPageShell";
import { detectionService } from "../services/detectionService";
import { detectionSettingsService } from "../services/detectionSettingsService";

export default function DetectionSettingsPage() {
  const [settings, setSettings] = useState(null);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [currentSettings, activeModels] = await Promise.all([
        detectionSettingsService.get(),
        detectionService.activeModels(),
      ]);
      setSettings(currentSettings);
      setModels(activeModels);
    } catch (requestError) {
      setError(requestError.message || "Could not load detection settings.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  function change(field, value) {
    setSaved(false);
    setSettings((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (saving || !settings) return;
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      const updated = await detectionSettingsService.update({
        ...settings,
        default_model_version_id: settings.default_model_version_id || null,
      });
      setSettings(updated);
      setSaved(true);
    } catch (requestError) {
      setError(requestError.message || "Settings could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <DetectionPageShell
      page="settings"
      title="Detection Settings"
      description="Configure the model version, risk thresholds, and data handling used by detection."
      loading={loading}
      error={error}
      onRefresh={loadSettings}
    >
      {settings && (
        <form className="det-settings-form" onSubmit={submit}>
          <section className="det-panel">
            <header>
              <div>
                <h2><ShieldCheck size={18}/> Model Configuration</h2>
                <p>Choose an active registered version or follow the latest activation.</p>
              </div>
            </header>
            <label className="det-field">
              <span>Default model version</span>
              <select
                value={settings.default_model_version_id || ""}
                disabled={saving}
                onChange={(event) => change("default_model_version_id", event.target.value || null)}
              >
                <option value="">Latest activated model (automatic)</option>
                {models.map((model) => (
                  <option key={model.model_version_id} value={model.model_version_id}>
                    {model.model_name} · {model.algorithm} · v{model.version}
                  </option>
                ))}
              </select>
              {!models.length && <small>There are no active model versions. Detection will remain unavailable until a version is activated.</small>}
            </label>
          </section>

          <section className="det-panel">
            <header>
              <div>
                <h2><Settings2 size={18}/> Risk Configuration</h2>
                <p>Thresholds are applied by the backend scoring service.</p>
              </div>
            </header>
            <div className="det-threshold-grid">
              <label className="det-field">
                <span>High risk threshold</span>
                <div className="det-number-field"><input type="number" min="1" max="99" value={settings.high_risk_threshold} disabled={saving} onChange={(event) => change("high_risk_threshold", Number(event.target.value))}/><small>Score 1–99</small></div>
              </label>
              <label className="det-field">
                <span>Critical risk threshold</span>
                <div className="det-number-field"><input type="number" min="2" max="100" value={settings.critical_risk_threshold} disabled={saving} onChange={(event) => change("critical_risk_threshold", Number(event.target.value))}/><small>Must exceed the high threshold</small></div>
              </label>
            </div>
          </section>

          <section className="det-panel">
            <header>
              <div>
                <h2>Detection Options</h2>
                <p>These choices control which additional results are analyzed or retained.</p>
              </div>
            </header>
            <label className="det-setting-toggle">
              <span><strong>Enable behavioral analysis</strong><small>Analyze sender history when enough email records are available.</small></span>
              <input type="checkbox" checked={settings.enable_behavioral_analysis} disabled={saving} onChange={(event) => change("enable_behavioral_analysis", event.target.checked)}/>
            </label>
            <label className="det-setting-toggle">
              <span><strong>Save feature snapshots</strong><small>Retain extracted features with detection results.</small></span>
              <input type="checkbox" checked={settings.save_feature_snapshots} disabled={saving} onChange={(event) => change("save_feature_snapshots", event.target.checked)}/>
            </label>
            <label className="det-setting-toggle">
              <span><strong>Store detection history</strong><small>Persist detection records, risk results, and analysis details.</small></span>
              <input type="checkbox" checked={settings.store_detection_history} disabled={saving} onChange={(event) => change("store_detection_history", event.target.checked)}/>
            </label>
          </section>

          <div className="det-settings-actions">
            {saved && <div className="det-success" role="status">Settings saved successfully.</div>}
            <button className="det-primary" type="submit" disabled={saving}>
              <Save size={16}/>{saving ? "Saving settings…" : "Save Settings"}
            </button>
          </div>
        </form>
      )}
    </DetectionPageShell>
  );
}
