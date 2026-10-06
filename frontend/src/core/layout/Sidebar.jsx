import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { canAccessPath } from "../permissions/roleAccess";

import {
  Activity,
  Bell,
  Archive,
  ServerCog,
  BookOpen,
  BrainCircuit,
  ChartNoAxesCombined,
  ChevronRight,
  ClipboardCheck,
  Cpu,
  Database,
  FileBarChart,
  FileSearch,
  FileText,
  FlaskConical,
  GitBranch,
  History,
  Layers3,
  LayoutDashboard,
  Mail,
  Network,
  RadioTower,
  Play,
  ScanSearch,
  Settings,
  Shield,
  ShieldAlert,
  ShieldCheck,
  SlidersHorizontal,
  Users,
  Workflow,
} from "lucide-react";

import "./Sidebar.css";

const navigationSections = [
  {
    title: "PLATFORM",
    items: [
      {
        label: "Dashboard",
        path: "/",
        icon: LayoutDashboard,
        enabled: true,
      },
    ],
  },

  {
    title: "EMAIL SECURITY",
    items: [
      {
        label: "Emails",
        path: "/emails",
        icon: Mail,
        enabled: true,
      },
    ],
  },

  {
    title: "EMAIL PARSING",
    items: [
      {
        label: "Parsing Workspace",
        path: "/parsing",
        icon: ScanSearch,
        enabled: true,
      },
    ],
  },

  {
    title: "FEATURE ENGINEERING",
    items: [
      {
        label: "Feature Workspace",
        path: "/features",
        icon: SlidersHorizontal,
        enabled: true,
        end: true,
      },
      {
        label: "Feature Definitions",
        path: "/features/definitions",
        icon: BookOpen,
        enabled: true,
      },
    ],
  },

  {
    title: "DATASET MANAGEMENT",
    items: [
      {
        label: "Dataset Workspace",
        path: "/datasets",
        icon: Database,
        enabled: true,
        end: true,
      },
      {
        label: "Datasets",
        path: "/datasets/list",
        icon: Archive,
        enabled: true,
      },
      {
        label: "Dataset Versions",
        path: "/datasets/versions",
        icon: GitBranch,
        enabled: true,
      },
      {
        label: "Dataset Validation",
        path: "/datasets/validation",
        icon: ClipboardCheck,
        enabled: true,
      },
      {
        label: "Dataset Export",
        path: "/datasets/export",
        icon: FileText,
        enabled: true,
      },
    ],
  },

  {
    title: "PREPROCESSING",
    items: [
      {
        label: "Preprocessing Pipeline",
        path: "/preprocessing",
        icon: Workflow,
        enabled: true,
        end: true,
      },
      {
        label: "Preprocessing History",
        path: "/preprocessing/runs",
        icon: History,
        enabled: true,
      },
    ],
  },

  {
    title: "ML MODEL MANAGEMENT",
    items: [
      {
        label: "Models",
        path: "/ml-models/models",
        icon: Cpu,
        enabled: true,
      },
      {
        label: "Training Runs",
        path: "/ml-models/training-runs",
        icon: Play,
        enabled: true,
      },
      {
        label: "Model Evaluation",
        path: "/ml-models/evaluation",
        icon: ChartNoAxesCombined,
        enabled: true,
      },
      {
        label: "Model Registry",
        path: "/ml-models/registry",
        icon: Layers3,
        enabled: true,
      },
    ],
  },

  {
    title: "DETECTION",
    items: [
      {
        label: "Detection Overview",
        path: "/detection",
        icon: ShieldCheck,
        enabled: true,
        end: true,
      },
      {
        label: "New Detection",
        path: "/detection/new",
        icon: Play,
        enabled: true,
      },
      {
        label: "Detection History",
        path: "/detection/history",
        icon: History,
        enabled: true,
      },
      {
        label: "Risk Analysis",
        path: "/detection/risk",
        icon: ShieldAlert,
        enabled: true,
      },
      {
        label: "Behavioral Analysis",
        path: "/detection/behavior",
        icon: Activity,
        enabled: true,
      },
      {
        label: "Detection Settings",
        path: "/detection/settings",
        icon: Settings,
        enabled: true,
      },
    ],
  },

  {
    title: "INVESTIGATION & REPORTING",
    items: [
      {
        label: "Explainability",
        path: "/explainability",
        icon: BrainCircuit,
        enabled: true,
      },
      {
        label: "Evidence Management",
        path: "/evidence",
        icon: FileSearch,
        enabled: true,
      },
      {
        label: "Reports",
        path: "/reports",
        icon: FileBarChart,
        enabled: true,
      },
    ],
  },

  {
    title: "ANALYTICS",
    items: [
      {
        label: "Analytics",
        path: "/analytics",
        icon: ChartNoAxesCombined,
        enabled: true,
      },
      {
        label: "Experiments",
        path: "/experiments",
        icon: FlaskConical,
        enabled: true,
      },
    ],
  },

  {
    title: "AUDIT & ADMIN",
    items: [
      { label: "Audit Logs", path: "/audit", icon: FileSearch, enabled: true },
      { label: "Security Monitoring", path: "/security-monitoring", icon: Bell, enabled: true },
      { label: "System Administration", path: "/administration", icon: ServerCog, enabled: true },
    ],
  },

  {
    title: "THREAT INTELLIGENCE",
    items: [
      {
        label: "Threat Overview",
        path: "/threat-intelligence",
        icon: Network,
        enabled: true,
      },
      {
        label: "Indicators",
        path: "/threat-intelligence/indicators",
        icon: FileSearch,
        enabled: true,
      },
      {
        label: "Threat Feeds",
        path: "/threat-intelligence/feeds",
        icon: RadioTower,
        enabled: true,
      },
      {
        label: "Threat Matches",
        path: "/threat-intelligence/matches",
        icon: ScanSearch,
        enabled: true,
      },
    ],
  },

  {
    title: "SYSTEM",
    items: [
      {
        label: "Users",
        path: "/users",
        icon: Users,
        enabled: true,
      },
      {
        label: "Settings",
        path: "/settings",
        icon: Settings,
        enabled: true,
      },
    ],
  },
];

function SidebarItem({ item }) {
  const Icon = item.icon;

  if (!item.enabled) {
    return (
      <div
        className="sidebar-item sidebar-item-disabled"
        aria-disabled="true"
        title={item.label}
      >
        <span className="sidebar-item-icon" aria-hidden="true">
          <Icon size={18} strokeWidth={1.8} />
        </span>

        <span className="sidebar-item-label">
          {item.label}
        </span>

      </div>
    );
  }

  return (
    <NavLink
      to={item.path}
      end={item.end ?? item.path === "/"}
      title={item.label}
      className={({ isActive }) =>
        `sidebar-item${isActive ? " sidebar-item-active" : ""}`
      }
    >
      <span className="sidebar-item-icon" aria-hidden="true">
        <Icon size={18} strokeWidth={1.8} />
      </span>

      <span className="sidebar-item-label">
        {item.label}
      </span>

      <ChevronRight
        className="sidebar-item-chevron"
        size={14}
        aria-hidden="true"
      />
    </NavLink>
  );
}

function SidebarSection({ section }) {
  const sectionId = `sidebar-section-${section.title
    .toLowerCase()
    .replace(/\s+/g, "-")}`;

  return (
    <section
      className="sidebar-section"
      aria-labelledby={sectionId}
    >
      <h2
        className="sidebar-section-title"
        id={sectionId}
      >
        {section.title}
      </h2>

      <div className="sidebar-section-items">
        {section.items.map((item) => (
          <SidebarItem
            key={`${section.title}-${item.label}`}
            item={item}
          />
        ))}
      </div>
    </section>
  );
}

function SidebarBrand() {
  return (
    <div className="sidebar-brand">
      <div
        className="sidebar-brand-mark"
        aria-hidden="true"
      >
        <Shield size={23} strokeWidth={2.2} />
      </div>

      <div className="sidebar-brand-content">
        <span className="sidebar-brand-title">
          Email Bomb Detection
        </span>

        <span className="sidebar-brand-subtitle">
          Security Platform
        </span>
      </div>
    </div>
  );
}

function SidebarFooter() {
  return (
    <div className="sidebar-footer">
      <div className="sidebar-footer-status">
        <span
          className="sidebar-status-indicator"
          aria-hidden="true"
        />

        <span>System Operational</span>
      </div>

      <span className="sidebar-version">
        v1.0
      </span>
    </div>
  );
}

export default function Sidebar() {
  const { user } = useAuth();
  const role = user?.role;
  const visibleSections = navigationSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => Boolean(role) && canAccessPath(role, item.path)),
    }))
    .filter((section) => section.items.length > 0);

  return (
    <aside
      className="app-sidebar"
      aria-label="Primary navigation"
    >
      <SidebarBrand />

      <nav
        className="sidebar-navigation"
        aria-label="Application sections"
      >
        {visibleSections.map((section) => (
          <SidebarSection
            key={section.title}
            section={section}
          />
        ))}
      </nav>

      <SidebarFooter />
    </aside>
  );
}
