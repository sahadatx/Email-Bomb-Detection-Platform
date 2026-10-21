
/**
 * Module 07 — ML Model Management
 *
 * Module metadata and page configuration.
 * Routes are registered by the application router.
 */

export const ML_MODELS_MODULE = Object.freeze({
  id: "ml-models",
  name: "ML Model Management",
  description:
    "Manage machine learning models, training runs, model versions, and evaluation results.",
  basePath: "/ml-models",
  version: "1.0.0",
  enabled: true,
});

// ============================================================================
// MODULE NAVIGATION
// ============================================================================

export const ML_MODELS_NAVIGATION = Object.freeze([
  {
    id: "models",
    label: "Models",
    path: "/ml-models/models",
    description: "Create and manage ML model definitions.",
  },
  {
    id: "training-runs",
    label: "Training Runs",
    path: "/ml-models/training-runs",
    description: "Create and monitor model training runs.",
  },
  {
    id: "evaluation",
    label: "Model Evaluation",
    path: "/ml-models/evaluation",
    description: "Evaluate model versions and inspect metrics.",
  },
  {
    id: "registry",
    label: "Model Registry",
    path: "/ml-models/registry",
    description: "Manage trained model versions and artifacts.",
  },
]);

// ============================================================================
// MODULE ROUTES
// ============================================================================

export const ML_MODELS_ROUTES = Object.freeze({
  MODELS: "/ml-models/models",
  TRAINING_RUNS: "/ml-models/training-runs",
  REGISTRY: "/ml-models/registry",
  EVALUATION: "/ml-models/evaluation",
});

// ============================================================================
// PAGE CONFIGURATION
// ============================================================================

export const ML_MODELS_PAGES = Object.freeze([
  {
    id: "models",
    name: "Models",
    path: ML_MODELS_ROUTES.MODELS,
    description: "Manage machine learning model definitions.",
    module: "ml-models",
  },
  {
    id: "training-runs",
    name: "Training Runs",
    path: ML_MODELS_ROUTES.TRAINING_RUNS,
    description: "Create and monitor model training executions.",
    module: "ml-models",
  },
  {
    id: "registry",
    name: "Model Registry",
    path: ML_MODELS_ROUTES.REGISTRY,
    description: "View and manage registered model versions.",
    module: "ml-models",
  },
  {
    id: "evaluation",
    name: "Model Evaluation",
    path: ML_MODELS_ROUTES.EVALUATION,
    description: "Create evaluation runs and view model metrics.",
    module: "ml-models",
  },
]);

// ============================================================================
// DEFAULT EXPORT
// ============================================================================

const mlModelsModule = Object.freeze({
  ...ML_MODELS_MODULE,
  navigation: ML_MODELS_NAVIGATION,
  routes: ML_MODELS_ROUTES,
  pages: ML_MODELS_PAGES,
});

export default mlModelsModule;
