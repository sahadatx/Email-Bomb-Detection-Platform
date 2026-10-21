/**
 * Module 06 — Preprocessing Pipeline
 *
 * Frontend module metadata and navigation configuration.
 *
 * Responsibilities:
 * - Dataset preprocessing
 * - Configuration validation
 * - Pipeline execution
 * - Execution results
 * - Preprocessing run history
 *
 * Dataset creation, versioning, splitting, and validation
 * remain the responsibility of Module 05.
 */

export const PREPROCESSING_MODULE_NAME = "preprocessing";

export const PREPROCESSING_MODULE_PREFIX = "/preprocessing";

export const PREPROCESSING_MODULE_VERSION = "1.0.0";

export const PREPROCESSING_ROUTES = Object.freeze({
  WORKSPACE: "/preprocessing",
  RUNS: "/preprocessing/runs",
  RUN_DETAILS: "/preprocessing/runs/:runId",
});

export const preprocessingNavigation = Object.freeze([
  {
    id: "preprocessing-workspace",
    label: "Preprocessing Pipeline",
    path: PREPROCESSING_ROUTES.WORKSPACE,
    icon: "workflow",
    end: true,
  },
  {
    id: "preprocessing-runs",
    label: "Preprocessing History",
    path: PREPROCESSING_ROUTES.RUNS,
    icon: "history",
  },
]);

export const preprocessingModule = Object.freeze({
  name: PREPROCESSING_MODULE_NAME,

  prefix: PREPROCESSING_MODULE_PREFIX,

  version: PREPROCESSING_MODULE_VERSION,

  title: "Preprocessing Pipeline",

  description:
    "Prepare, validate, transform, and track validated dataset versions before model training.",

  basePath: PREPROCESSING_MODULE_PREFIX,

  navigation: preprocessingNavigation,

  routes: PREPROCESSING_ROUTES,

  capabilities: Object.freeze({
    datasetSelection: true,
    validatedDatasetsOnly: true,
    readOnlySplitConfiguration: true,
    schemaValidation: true,
    missingValueHandling: true,
    featureScaling: true,
    duplicateDetection: true,
    pipelineExecution: true,
    artifactManagement: true,
    runHistory: true,
    runDetails: true,
    datasetCreation: false,
    versionCreation: false,
    splitEditing: false,
    datasetValidation: false,
    modelTraining: false,
    prediction: false,
  }),
});

export default preprocessingModule;