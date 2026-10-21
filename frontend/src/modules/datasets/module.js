
import {
  DATASET_MODULE,
  DATASET_ROUTES,
} from "./types";

/**
 * Module 05 — Dataset Management
 *
 * Frontend module metadata and navigation configuration.
 *
 * Sidebar structure:
 * - Dataset Workspace
 * - Datasets
 * - Dataset Versions
 * - Dataset Validation
 * - Dataset Export
 *
 * Split configuration is part of Create Version.
 * Dataset creation is initiated from Dataset Workspace.
 */

export const datasetNavigation = Object.freeze([
  {
    id: "dataset-workspace",
    label: "Dataset Workspace",
    path: DATASET_ROUTES.WORKSPACE,
    icon: "layout-dashboard",
    end: true,
  },
  {
    id: "datasets",
    label: "Datasets",
    path: DATASET_ROUTES.LIST,
    icon: "database",
  },
  {
    id: "dataset-versions",
    label: "Dataset Versions",
    path: DATASET_ROUTES.VERSIONS,
    icon: "git-branch",
  },
  {
    id: "dataset-validation",
    label: "Dataset Validation",
    path: DATASET_ROUTES.VALIDATION,
    icon: "shield-check",
  },
  {
    id: "dataset-export",
    label: "Dataset Export",
    path: DATASET_ROUTES.EXPORT,
    icon: "download",
  },
]);

export const datasetModule = Object.freeze({
  name: DATASET_MODULE.NAME,
  version: DATASET_MODULE.VERSION,
  title: "Dataset Management",
  description:
    "Manage feature-extracted emails and prepare immutable, ML-ready datasets.",
  basePath: DATASET_MODULE.BASE_PATH,
  navigation: datasetNavigation,
  routes: DATASET_ROUTES,
  capabilities: Object.freeze({
    workspace: true,
    datasetCreation: true,
    versioning: true,
    splitting: true,
    validation: true,
    export: true,
    featureRecalculation: false,
    prediction: false,
    riskScoring: false,
  }),
});

export default datasetModule;