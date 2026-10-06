import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

// ============================================================================
// APPLICATION FOUNDATION
// ============================================================================

import ProtectedRoute, { RoleGuard } from "../auth/ProtectedRoute";
import Unauthorized from "../auth/Unauthorized";
import AppLayout from "../layout/AppLayout";

// ============================================================================
// AUTHENTICATION — MODULE FOUNDATION
// ============================================================================

import Login from "../../modules/auth/pages/Login";

// ============================================================================
// USER MANAGEMENT — MODULE 01
// ============================================================================

import UserList from "../../modules/users/pages/UserList";
import ProfilePage from "../../modules/users/pages/ProfilePage";

// ============================================================================
// EMAIL COLLECTION & INGESTION — MODULE 02
// ============================================================================

import EmailOverview from "../../modules/emails/pages/EmailOverview";

// ============================================================================
// EMAIL PARSING & NORMALIZATION — MODULE 03
// ============================================================================

import ParsingWorkspace from "../../modules/parsing/pages/ParsingWorkspace";
import ParsedEmail from "../../modules/parsing/pages/ParsedEmail";

// ============================================================================
// FEATURE ENGINEERING — MODULE 04
// ============================================================================

import FeatureWorkspace from "../../modules/features/pages/FeatureWorkspace";
import FeatureDetails from "../../modules/features/pages/FeatureDetails";
import FeatureDefinitions from "../../modules/features/pages/FeatureDefinitions";

// ============================================================================
// DATASET MANAGEMENT — MODULE 05
// ============================================================================

import DatasetWorkspace from "../../modules/datasets/pages/DatasetWorkspace";
import DatasetList from "../../modules/datasets/pages/DatasetList";
import DatasetVersions from "../../modules/datasets/pages/DatasetVersions";
import DatasetValidation from "../../modules/datasets/pages/DatasetValidation";
import DatasetExport from "../../modules/datasets/pages/DatasetExport";

// ============================================================================
// PREPROCESSING PIPELINE — MODULE 06
// ============================================================================

import PreprocessingWorkspace from "../../modules/preprocessing/pages/PreprocessingWorkspace";
import PreprocessingHistory from "../../modules/preprocessing/pages/PreprocessingHistory";

// ============================================================================
// ML MODEL MANAGEMENT — MODULE 07
// ============================================================================

import ModelsPage from "../../modules/ml-models/pages/ModelsPage";
import TrainingRunsPage from "../../modules/ml-models/pages/TrainingRunsPage";
import ModelRegistryPage from "../../modules/ml-models/pages/ModelRegistryPage";
import ModelEvaluationPage from "../../modules/ml-models/pages/ModelEvaluationPage";
import {
  DetectionOverviewPage,
  NewDetectionPage,
  DetectionHistoryPage,
  RiskAnalysisPage,
  BehavioralAnalysisPage,
  DetectionSettingsPage,
} from "../../modules/detection/module";
import {
  ExplainabilityPage,
  EvidencePage,
  ReportsPage,
  ReportDetailsPage,
} from "../../modules/investigation-reporting/module";
import {
  AuditLogsPage,
  SecurityMonitoringPage,
  SystemAdministrationPage,
} from "../../modules/audit-security-admin/module";
import { AnalyticsPage } from "../../modules/analytics/module";
import {
  ExperimentsPage,
  CreateExperimentPage,
  ExperimentDetailsPage,
  ExperimentRunDetailsPage,
} from "../../modules/experiments/module";
import {
  ThreatOverviewPage,
  IndicatorsPage,
  ThreatFeedsPage,
  ThreatMatchesPage,
} from "../../modules/threat_intelligence/module";
import { DashboardPage } from "../../modules/dashboard/module";
import { SettingsPage } from "../../modules/settings/module";

// ============================================================================
// MODULE STYLES
// ============================================================================

import "../../modules/emails/styles/emails.css";
import "../../modules/parsing/styles/parsing.css";
import "../../modules/features/styles/features.css";
import "../../modules/datasets/styles/datasets.css";
import "../../modules/preprocessing/styles/preprocessing.css";
import "../../modules/ml-models/styles/ml-models.css";
import "../../modules/detection/styles/detection.css";
import "../../modules/investigation-reporting/styles/investigation-reporting.css";
import "../../modules/audit-security-admin/styles/audit-security-admin.css";
import "../../modules/analytics/styles/analytics.css";
import "../../modules/experiments/styles/experiments.css";

// ============================================================================
// APPLICATION FOUNDATION
// ============================================================================

// ============================================================================
// APPLICATION ROUTER
// ============================================================================

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ==================================================================
            PUBLIC ROUTES
        ================================================================== */}

        <Route path="/login" element={<Login />} />

        {/* ==================================================================
            PROTECTED APPLICATION
        ================================================================== */}

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            {/* ==============================================================
                APPLICATION ROOT
            ============================================================== */}

            <Route path="/" element={<DashboardPage />} />
            <Route path="/settings" element={<Navigate to="/settings/general" replace />} />
            <Route path="/settings/:category" element={<SettingsPage />} />

            {/* ==============================================================
                EMAIL SECURITY — MODULE 02
            ============================================================== */}

            <Route path="/emails" element={<EmailOverview />} />

            {/* ==============================================================
                EMAIL PARSING & NORMALIZATION — MODULE 03
            ============================================================== */}

            <Route path="/parsing" element={<ParsingWorkspace />} />

            <Route path="/parsing/emails/:emailId" element={<ParsedEmail />} />

            {/* ==============================================================
                FEATURE ENGINEERING — MODULE 04
            ============================================================== */}

            <Route path="/features" element={<FeatureWorkspace />} />

            <Route
              path="/features/definitions"
              element={<FeatureDefinitions />}
            />

            <Route path="/features/:emailId" element={<FeatureDetails />} />

            {/* ==============================================================
                DATASET MANAGEMENT — MODULE 05
            ============================================================== */}

            <Route path="/datasets" element={<DatasetWorkspace />} />

            <Route path="/datasets/list" element={<DatasetList />} />

            <Route path="/datasets/versions" element={<DatasetVersions />} />

            <Route
              path="/datasets/validation"
              element={<DatasetValidation />}
            />

            <Route path="/datasets/export" element={<DatasetExport />} />

            {/* ==============================================================
                PREPROCESSING PIPELINE — MODULE 06
            ============================================================== */}

            <Route path="/preprocessing" element={<PreprocessingWorkspace />} />

            <Route
              path="/preprocessing/runs"
              element={<PreprocessingHistory />}
            />

            {/* ==============================================================
                ML MODEL MANAGEMENT — MODULE 07
            ============================================================== */}

            <Route
              path="/ml-models"
              element={<Navigate to="/ml-models/models" replace />}
            />

            <Route path="/ml-models/models" element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST", "VIEWER"]}><ModelsPage /></RoleGuard>} />

            <Route
              path="/ml-models/training-runs"
              element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><TrainingRunsPage /></RoleGuard>}
            />

            <Route path="/ml-models/registry" element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST", "VIEWER"]}><ModelRegistryPage /></RoleGuard>} />

            <Route
              path="/ml-models/evaluation"
              element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST", "VIEWER"]}><ModelEvaluationPage /></RoleGuard>}
            />

            {/* DETECTION & RISK ANALYSIS — MODULE 08 */}
            <Route path="/detection" element={<DetectionOverviewPage />} />
            <Route path="/detection/new" element={<NewDetectionPage />} />
            <Route
              path="/detection/history"
              element={<DetectionHistoryPage />}
            />
            <Route path="/detection/risk" element={<RiskAnalysisPage />} />
            <Route
              path="/detection/behavior"
              element={<BehavioralAnalysisPage />}
            />
            <Route
              path="/detection/settings"
              element={<RoleGuard roles={["ADMIN"]}><DetectionSettingsPage /></RoleGuard>}
            />

            {/* INVESTIGATION & REPORTING */}
            <Route path="/explainability" element={<ExplainabilityPage />} />
            <Route path="/evidence" element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><EvidencePage /></RoleGuard>} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/reports/:reportId" element={<ReportDetailsPage />} />

            {/* AUDIT, SECURITY MONITORING & ADMINISTRATION — MODULE 09 */}
            <Route path="/audit" element={<RoleGuard roles={["ADMIN"]}><AuditLogsPage /></RoleGuard>} />
            <Route
              path="/security-monitoring"
              element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><SecurityMonitoringPage /></RoleGuard>}
            />
            <Route
              path="/administration"
              element={<RoleGuard roles={["ADMIN"]}><SystemAdministrationPage /></RoleGuard>}
            />

            {/* ANALYTICS & EXPERIMENTS */}
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/experiments" element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><ExperimentsPage /></RoleGuard>} />
            <Route path="/experiments/new" element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><CreateExperimentPage /></RoleGuard>} />
            <Route
              path="/experiments/:experimentId"
              element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><ExperimentDetailsPage /></RoleGuard>}
            />
            <Route
              path="/experiments/:experimentId/runs/:runId"
              element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><ExperimentRunDetailsPage /></RoleGuard>}
            />

            {/* THREAT INTELLIGENCE — MODULE 10 */}
            <Route
              path="/threat-intelligence"
              element={<ThreatOverviewPage />}
            />
            <Route
              path="/threat-intelligence/indicators"
              element={<IndicatorsPage />}
            />
            <Route
              path="/threat-intelligence/feeds"
              element={<RoleGuard roles={["ADMIN", "SECURITY_ANALYST"]}><ThreatFeedsPage /></RoleGuard>}
            />
            <Route
              path="/threat-intelligence/matches"
              element={<ThreatMatchesPage />}
            />

            {/* ==============================================================
                USER MANAGEMENT — MODULE 01
            ============================================================== */}

            <Route path="/users" element={<RoleGuard roles={["ADMIN"]}><UserList /></RoleGuard>} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            <Route path="/users/*" element={<Navigate to="/users" replace />} />
          </Route>
        </Route>

        {/* ==================================================================
            UNKNOWN ROUTES
        ================================================================== */}

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
