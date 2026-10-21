
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../../core/auth/AuthProvider";

import {
  RefreshCw,
  Workflow,
} from "lucide-react";

import DatasetSelector from "../components/DatasetSelector";
import SplitInformation from "../components/SplitInformation";
import PreprocessingConfiguration from "../components/PreprocessingConfiguration";
import PipelineExecution from "../components/PipelineExecution";
import PreprocessingOverview from "../components/PreprocessingOverview";

import { DEFAULT_PREPROCESSING_CONFIG } from "../types";
import datasetService from "../../datasets/services/datasetService";
import {
  getPreprocessingErrorMessage,
  getPreprocessingSummary,
} from "../services/preprocessingService";

function createDefaultConfiguration() {
  return {
    ...DEFAULT_PREPROCESSING_CONFIG,
    feature_order: [
      ...(DEFAULT_PREPROCESSING_CONFIG.feature_order ?? []),
    ],
    scaling_features: [
      ...(DEFAULT_PREPROCESSING_CONFIG.scaling_features ?? []),
    ],
  };
}

function unwrapResponse(value) {
  let current = value;

  for (let i = 0; i < 3; i += 1) {
    if (
      current &&
      typeof current === "object" &&
      !Array.isArray(current) &&
      current.data &&
      typeof current.data === "object"
    ) {
      current = current.data;
      continue;
    }

    break;
  }

  return current;
}

function getDatasetVersion(selection) {
  if (!selection || typeof selection !== "object") {
    return null;
  }

  const source = unwrapResponse(selection);

  return (
    source?.dataset_version ??
    source?.version ??
    source?.selected_version ??
    source?.datasetVersion ??
    source
  );
}

function getDatasetVersionId(selection) {
  const source = unwrapResponse(selection);
  const version = getDatasetVersion(source);

  const id =
    version?.id ??
    version?.version_id ??
    version?.dataset_version_id ??
    source?.dataset_version_id ??
    source?.version_id ??
    source?.selected_version_id ??
    "";

  return typeof id === "string" ? id : String(id || "");
}

function getValidationResult(result) {
  const source = unwrapResponse(result);

  return Boolean(
    source?.valid ??
    source?.is_valid ??
    source?.success ??
    source?.validation_passed ??
    false
  );
}

export default function PreprocessingWorkspace() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);
  const [datasetSelection, setDatasetSelection] = useState(null);

  const [configuration, setConfiguration] = useState(
    createDefaultConfiguration
  );

  const [configurationValidated, setConfigurationValidated] =
    useState(false);

  const [datasetSelectorKey, setDatasetSelectorKey] = useState(0);

  const [refreshing, setRefreshing] = useState(false);
  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overviewError, setOverviewError] = useState("");

  const loadOverview = useCallback(async () => {
    setOverviewLoading(true);
    setOverviewError("");

    try {
      const [runSummary, datasetPage] = await Promise.all([
        getPreprocessingSummary(),
        datasetService.getDatasets({ page: 1, page_size: 1 }),
      ]);

      setOverview({
        available_datasets: Number(
          datasetPage?.pagination?.total ?? 0
        ),
        total_runs: Number(runSummary?.total ?? 0),
        successful_runs: Number(runSummary?.completed ?? 0),
        failed_runs: Number(runSummary?.failed ?? 0),
      });
    } catch (error) {
      setOverview(null);
      setOverviewError(
        getPreprocessingErrorMessage(error) ||
          "Unable to load preprocessing overview."
      );
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  const datasetVersionId = useMemo(
    () => getDatasetVersionId(datasetSelection),
    [datasetSelection]
  );

  const handleDatasetSelection = useCallback((selection) => {
    setDatasetSelection(selection ?? null);
    setConfigurationValidated(false);
  }, []);

  const handleConfigurationChange = useCallback((nextConfig) => {
    setConfiguration(nextConfig);
    setConfigurationValidated(false);
  }, []);

  const handleValidationChange = useCallback((result) => {
    setConfigurationValidated(getValidationResult(result));
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    setDatasetSelection(null);
    setConfigurationValidated(false);
    setConfiguration(createDefaultConfiguration());
    setDatasetSelectorKey((current) => current + 1);
    try {
      await loadOverview();
    } finally {
      setRefreshing(false);
    }
  }, [loadOverview]);

  return (
    <main className="preprocessing-workspace">
      <header className="preprocessing-workspace-header">
        <div className="preprocessing-workspace-title">
          <div className="preprocessing-workspace-icon">
            <Workflow size={25} aria-hidden="true" />
          </div>

          <div>
            <div className="preprocessing-workspace-eyebrow">
              DATA PREPARATION
            </div>

            <h1>Preprocessing Pipeline</h1>

            <p>
              Prepare, validate, transform, and track dataset versions.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="preprocessing-secondary-button"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw
            size={16}
            aria-hidden="true"
            className={refreshing ? "is-spinning" : ""}
          />
          Refresh
        </button>
      </header>

      <PreprocessingOverview
        stats={overview}
        loading={overviewLoading}
        error={overviewError}
      />

      <div className="preprocessing-workspace-layout">
        <div className="preprocessing-workspace-main">
          <DatasetSelector
            key={datasetSelectorKey}
            value={datasetVersionId}
            onSelectionChange={handleDatasetSelection}
          />

          <SplitInformation selection={datasetSelection} />

          <PreprocessingConfiguration
            value={configuration}
            onChange={handleConfigurationChange}
            datasetVersionId={datasetVersionId}
            onValidationChange={handleValidationChange}
            disabled={!canManage || !datasetVersionId}
            readOnly={!canManage}
          />
        </div>

        <aside
          className="preprocessing-workspace-sidebar"
          aria-label="Pipeline execution"
        >
          <PipelineExecution
            datasetVersionId={datasetVersionId}
            config={configuration}
            configurationValidated={configurationValidated}
          disabled={!datasetVersionId || !configurationValidated}
          canManage={canManage}
          />
        </aside>
      </div>
    </main>
  );
}
