import { useEffect, useState } from "react";
import { FileText, Mail, Play, Upload } from "lucide-react";
import { detectionService } from "../services/detectionService";
import { detectionSettingsService } from "../services/detectionSettingsService";

const MAX_FILES = 20;
const MAX_FILE_BYTES = 20_000_000;

export default function NewDetectionForm({ onComplete }) {
  const [inputMode, setInputMode] = useState("email");
  const [emails, setEmails] = useState([]);
  const [emailIds, setEmailIds] = useState([]);
  const [emailSearch, setEmailSearch] = useState("");
  const [rawEmail, setRawEmail] = useState("");
  const [files, setFiles] = useState([]);
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [risk, setRisk] = useState(true);
  const [behavior, setBehavior] = useState(true);
  const [behaviorEnabled, setBehaviorEnabled] = useState(true);

  useEffect(() => {
    let mounted = true;
    Promise.all([detectionService.emails(), detectionService.activeModel(), detectionSettingsService.get()])
      .then(([list, active, settings]) => {
        if (!mounted) return;
        setEmails(list.filter((item) => item.has_features));
        setModel(active);
        setBehaviorEnabled(settings.enable_behavioral_analysis);
        setBehavior(settings.enable_behavioral_analysis);
      })
      .catch((e) => { if (mounted) setError(e.message || "Could not load detection options."); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  function selectFiles(fileList) {
    setError("");
    const selected = Array.from(fileList || []);
    if (selected.length > MAX_FILES) {
      setFiles([]); setError(`Select no more than ${MAX_FILES} .eml files at a time.`); return;
    }
    const invalid = selected.find((file) => !file.name.toLowerCase().endsWith(".eml") || file.size > MAX_FILE_BYTES);
    if (invalid) {
      setFiles([]);
      setError(!invalid.name.toLowerCase().endsWith(".eml") ? `${invalid.name} is not an .eml file.` : `${invalid.name} is larger than 20 MB.`);
      return;
    }
    setFiles(selected);
  }

  async function submit(event) {
    event.preventDefault();
    if (busy || loading || !model?.available) return;
    setBusy(true); setError("");
    try {
      const options = {
        model_version_id: model.model_version_id,
        run_behavioral_analysis: behavior,
        calculate_risk_score: risk,
      };
      let result;
      if (inputMode === "raw") {
        result = await detectionService.createRaw({ raw_email: rawEmail, filename: "pasted-email.eml", ...options });
      } else if (inputMode === "upload") {
        result = files.length === 1
          ? await detectionService.upload(files[0], options)
          : await detectionService.uploadBatch(files, options);
      } else {
        result = emailIds.length === 1
          ? await detectionService.create({ email_id: emailIds[0], ...options })
          : await detectionService.createBatch({ email_ids: emailIds, ...options });
      }
      onComplete(result);
      setEmailIds([]); setFiles([]); setRawEmail("");
    } catch (e) { setError(e.message || "Detection could not be completed."); } finally { setBusy(false); }
  }

  const canSubmit = inputMode === "email" ? emailIds.length > 0 : inputMode === "raw" ? rawEmail.trim().length >= 20 : files.length > 0;
  const filteredEmails = emails.filter((email) => `${email.sender || ""} ${email.subject || ""}`.toLowerCase().includes(emailSearch.trim().toLowerCase()));
  const activeInputCount = inputMode === "email" ? emailIds.length : inputMode === "upload" ? files.length : 1;

  return (
    <form className="det-form" onSubmit={submit}>
      <div className="det-mode">
        <button type="button" className={inputMode === "email" ? "selected" : ""} onClick={() => setInputMode("email")}><Mail size={16}/> Existing emails</button>
        <button type="button" className={inputMode === "upload" ? "selected" : ""} onClick={() => setInputMode("upload")}><Upload size={16}/> .eml files</button>
        <button type="button" className={inputMode === "raw" ? "selected" : ""} onClick={() => setInputMode("raw")}><FileText size={16}/> Raw email</button>
      </div>

      {loading && <div className="det-loading">Loading email and model options…</div>}

      {inputMode === "email" ? (
        <label>Emails from collection
          <details className="det-email-dropdown">
            <summary aria-disabled={loading || busy}>
              <span>{emailIds.length ? `${emailIds.length} email${emailIds.length === 1 ? "" : "s"} selected` : "Select existing emails"}</span>
              <span aria-hidden="true">▾</span>
            </summary>
            <div className="det-email-dropdown__menu">
              <input type="search" value={emailSearch} placeholder="Search sender or subject" aria-label="Search existing emails" disabled={loading || busy} onChange={(event) => setEmailSearch(event.target.value)} />
              <div className="det-email-dropdown__options">
                {filteredEmails.map((email) => <label className="det-email-option" key={email.id}>
                  <input type="checkbox" checked={emailIds.includes(email.id)} disabled={loading || busy} onChange={(event) => setEmailIds((current) => event.target.checked ? [...current, email.id] : current.filter((id) => id !== email.id))} />
                  <span><strong>{email.subject || "(No subject)"}</strong><small>{email.sender || "Unknown sender"}</small></span>
                </label>)}
                {filteredEmails.length === 0 && <p className="det-email-dropdown__empty">{emails.length ? "No matching emails." : "No emails with extracted features are available."}</p>}
              </div>
            </div>
          </details>
          <small>Select one email or several emails for batch detection.</small>
        </label>
      ) : inputMode === "raw" ? (
        <label>Raw email source
          <textarea className="det-raw-email" required rows={12} value={rawEmail} placeholder={"Paste the complete raw email including headers, a blank line, and the message body."} disabled={loading || busy} onChange={(event) => setRawEmail(event.target.value)} />
          <small>Paste the complete RFC 822 email. It will be parsed and features will be extracted before prediction.</small>
        </label>
      ) : (
        <label className="det-upload">{files.length ? `${files.length} .eml file${files.length === 1 ? "" : "s"} selected` : "Choose one or more .eml files"}
          <input type="file" accept=".eml,message/rfc822" multiple required disabled={loading || busy} onChange={(event) => selectFiles(event.target.files)} />
          <small>Up to {MAX_FILES} files, maximum 20 MB each.</small>
        </label>
      )}

      <div className="det-model-select"><small>Active model version</small><strong>{loading ? "Loading…" : model?.available ? `${model.model_name} · ${model.algorithm} · v${model.version}` : "No active model version"}</strong>{!loading && !model?.available && <span>Register a completed training run and activate its version before detection.</span>}</div>
      <label className="det-check"><input type="checkbox" checked={risk} disabled={busy} onChange={(e) => setRisk(e.target.checked)}/> Calculate risk score</label>
      <label className="det-check"><input type="checkbox" checked={behavior} disabled={busy || !behaviorEnabled} onChange={(e) => setBehavior(e.target.checked)}/> Run behavioral analysis{!behaviorEnabled && <small>Disabled in Detection Settings.</small>}</label>
      {error && <div className="det-error" role="alert">{error}</div>}
      <div className="det-form-actions"><button className="det-primary" disabled={busy || loading || !model?.available || !canSubmit}><Play size={16}/>{busy ? "Analyzing…" : activeInputCount > 1 ? `Run ${activeInputCount} Detections` : "Run Detection"}</button></div>
    </form>
  );
}
