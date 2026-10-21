import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  Database,
  Download,
  FileDown,
  RefreshCw,
} from "lucide-react";

import "../styles/datasets.css";

import datasetService from "../services/datasetService";
import DatasetExportPanel from "../components/DatasetExportPanel";

function getItems(response) {
  if (Array.isArray(response)) return response;

  return (
    response?.items ??
    response?.datasets ??
    response?.versions ??
    response?.results ??
    response?.data?.items ??
    response?.data?.datasets ??
    response?.data?.versions ??
    []
  );
}

function getErrorMessage(error, fallback) {
  return (
    error?.response?.data?.detail ??
    error?.detail ??
    error?.message ??
    fallback
  );
}

function getDatasetId(dataset) {
  return dataset?.dataset_id ?? dataset?.id ?? "";
}

function getVersionId(version) {
  return version?.version_id ?? version?.id ?? "";
}

function getFilenameFromDisposition(disposition, fallback) {
  if (!disposition) return fallback;

  const utf8Match = disposition.match(
    /filename\*=UTF-8''([^;]+)/i
  );

  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(
        utf8Match[1].trim().replace(/^["']|["']$/g, "")
      );
    } catch {
      return fallback;
    }
  }

  const filenameMatch = disposition.match(
    /filename="?([^";]+)"?/i
  );

  return filenameMatch?.[1]?.trim() || fallback;
}

function getExportBlob(result) {
  if (result instanceof Blob) return result;
  if (result?.blob instanceof Blob) return result.blob;
  if (result?.data instanceof Blob) return result.data;

  return null;
}

function getExportHeaders(result) {
  return result?.headers ?? result?.response?.headers ?? {};
}

function sanitizeFilenamePart(value) {
  return String(value ?? "")
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 100);
}

function buildFallbackFilename({
  dataset,
  version,
  split,
  format,
  versionId,
}) {
  const datasetName =
    dataset?.name ??
    dataset?.dataset_name ??
    "dataset";

  const versionName =
    version?.name ??
    version?.version_name ??
    versionId ??
    "version";

  const safeDataset = sanitizeFilenamePart(datasetName) || "dataset";
  const safeVersion = sanitizeFilenamePart(versionName) || "version";
  const safeSplit = sanitizeFilenamePart(split) || "all";
  const extension = format === "json" ? "json" : "csv";

  return `${safeDataset}-${safeVersion}-${safeSplit}.${extension}`;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = "none";

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  // Allow the browser to start the download before releasing the URL.
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function DatasetExport() {
  const [datasets, setDatasets] = useState([]);
  const [versions, setVersions] = useState([]);

  const [datasetId, setDatasetId] = useState("");
  const [versionId, setVersionId] = useState("");
  const [format, setFormat] = useState("csv");
  const [split, setSplit] = useState("all");

  const [loading, setLoading] = useState(true);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const [error, setError] = useState("");
  const [exportError, setExportError] = useState("");
  const [exportMessage, setExportMessage] = useState("");

  const versionRequestRef = useRef(0);

  const selectedDataset = useMemo(
    () =>
      datasets.find(
        (item) => String(getDatasetId(item)) === String(datasetId)
      ) ?? null,
    [datasets, datasetId]
  );

  const selectedVersion = useMemo(
    () =>
      versions.find(
        (item) => String(getVersionId(item)) === String(versionId)
      ) ?? null,
    [versions, versionId]
  );

  const loadDatasets = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await datasetService.listDatasets({
        page: 1,
        page_size: 1000,
      });

      setDatasets(getItems(response));
    } catch (err) {
      setDatasets([]);
      setError(getErrorMessage(err, "Unable to load datasets."));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadVersions = useCallback(async (selectedId) => {
    const requestId = ++versionRequestRef.current;

    if (!selectedId) {
      setVersions([]);
      setVersionId("");
      setVersionsLoading(false);
      return;
    }

    setVersionsLoading(true);
    setExportError("");
    setExportMessage("");

    try {
      const response = await datasetService.listVersions({
        dataset_id: selectedId,
        page: 1,
        page_size: 1000,
      });

      // Ignore results from an outdated dataset selection.
      if (requestId !== versionRequestRef.current) return;

      const items = getItems(response);
      setVersions(items);

      setVersionId((current) => {
        const stillExists = items.some(
          (version) =>
            String(getVersionId(version)) === String(current)
        );

        return current && stillExists ? current : "";
      });
    } catch (err) {
      if (requestId !== versionRequestRef.current) return;

      setVersions([]);
      setVersionId("");
      setExportError(
        getErrorMessage(err, "Unable to load dataset versions.")
      );
    } finally {
      if (requestId === versionRequestRef.current) {
        setVersionsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadDatasets();

    return () => {
      versionRequestRef.current += 1;
    };
  }, [loadDatasets]);

  useEffect(() => {
    setVersions([]);
    setVersionId("");
    setExportError("");
    setExportMessage("");

    if (datasetId) {
      loadVersions(datasetId);
    } else {
      versionRequestRef.current += 1;
      setVersionsLoading(false);
    }
  }, [datasetId, loadVersions]);

  const handleDatasetChange = useCallback((nextDatasetId) => {
    versionRequestRef.current += 1;

    setDatasetId(nextDatasetId);
    setVersionId("");
    setVersions([]);
    setVersionsLoading(false);
    setExportError("");
    setExportMessage("");
  }, []);

  const handleVersionChange = useCallback((nextVersionId) => {
    setVersionId(nextVersionId);
    setExportError("");
    setExportMessage("");
  }, []);

  const handleExport = useCallback(async () => {
    if (!datasetId || !versionId || exporting) return;

    setExporting(true);
    setExportError("");
    setExportMessage("");

    try {
      const result = await datasetService.exportDataset({
        dataset_id: datasetId,
        version_id: versionId,
        format,
        split,
      });

      const blob = getExportBlob(result);

      if (!blob) {
        throw new Error(
          "The export service did not return a downloadable file."
        );
      }

      const fallbackFilename = buildFallbackFilename({
        dataset: selectedDataset,
        version: selectedVersion,
        split,
        format,
        versionId,
      });

      const headers = getExportHeaders(result);
      const disposition =
        headers["content-disposition"] ??
        headers["Content-Disposition"];

      const filename =
        result?.filename ??
        getFilenameFromDisposition(disposition, fallbackFilename);

      downloadBlob(blob, filename);
      setExportMessage(`Export started: ${filename}`);
    } catch (err) {
      setExportError(
        getErrorMessage(err, "Dataset export failed.")
      );
    } finally {
      setExporting(false);
    }
  }, [
    datasetId,
    versionId,
    exporting,
    format,
    split,
    selectedDataset,
    selectedVersion,
  ]);

  const handleRefresh = useCallback(async () => {
    setExportError("");
    setExportMessage("");

    await loadDatasets();

    if (datasetId) {
      await loadVersions(datasetId);
    }
  }, [datasetId, loadDatasets, loadVersions]);

  return (
    <main className="dataset-export-page">
      <header className="dataset-page-header">
        <div className="dataset-page-header__title">
          <div className="dataset-page-header__icon">
            <FileDown size={22} />
          </div>

          <div>
            <h1>Dataset Export</h1>
            <p>
              Export immutable dataset versions for machine learning
              and offline analysis.
            </p>
          </div>
        </div>

        <div className="dataset-export-page__header-actions">
          <button
            type="button"
            className="dataset-button dataset-button--secondary"
            onClick={handleRefresh}
            disabled={loading || versionsLoading || exporting}
          >
            <RefreshCw
              size={16}
              className={
                loading || versionsLoading
                  ? "dataset-icon--spinning"
                  : ""
              }
            />
            Refresh
          </button>
        </div>
      </header>

      {error && (
        <div className="dataset-workspace__error" role="alert">
          <AlertCircle size={18} />
          <span>{error}</span>

          <button
            type="button"
            className="dataset-button dataset-button--ghost"
            onClick={loadDatasets}
            disabled={loading}
          >
            Retry
          </button>
        </div>
      )}

      {exportError && (
        <div className="dataset-workspace__error" role="alert">
          <AlertCircle size={18} />
          <span>{exportError}</span>
        </div>
      )}

      {exportMessage && (
        <div
          className="dataset-export-page__success"
          role="status"
        >
          <Download size={18} />
          <span>{exportMessage}</span>
        </div>
      )}

      {!loading && datasets.length === 0 && !error ? (
        <section className="dataset-export-page__empty">
          <Database size={30} />
          <h2>No datasets available</h2>
          <p>
            Create a dataset and at least one version before
            exporting.
          </p>
        </section>
      ) : (
        <div className="dataset-export-page__content">
          <DatasetExportPanel
            datasets={datasets}
            versions={versions}
            datasetId={datasetId}
            versionId={versionId}
            format={format}
            split={split}
            loading={loading || versionsLoading}
            exporting={exporting}
            error={exportError}
            onDatasetChange={handleDatasetChange}
            onVersionChange={handleVersionChange}
            onFormatChange={setFormat}
            onSplitChange={setSplit}
            onExport={handleExport}
          />

          <aside className="dataset-export-page__information">
            <div className="dataset-export-page__information-header">
              <FileDown size={19} />
              <h2>Export Information</h2>
            </div>

            <div className="dataset-export-page__information-body">
              <p>
                The exported file represents the selected dataset
                version and split.
              </p>

              <ul>
                <li>CSV and JSON output formats</li>
                <li>Entire dataset or individual splits</li>
                <li>Canonical ground-truth labels</li>
                <li>Canonical F1–F12 feature values</li>
                <li>Split membership for version samples</li>
              </ul>

              <p className="dataset-export-page__information-note">
                Export does not recalculate features or alter
                the source dataset version.
              </p>
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}