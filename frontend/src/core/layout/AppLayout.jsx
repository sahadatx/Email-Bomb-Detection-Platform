import { Navigate, Outlet, useLocation } from "react-router-dom";

import Header from "./Header";
import Sidebar from "./Sidebar";
import { useAuth } from "../auth/AuthProvider";
import { canAccessPath } from "../permissions/roleAccess";

import "./AppLayout.css";

export default function AppLayout() {
  const { user } = useAuth();
  const location = useLocation();
  if (!canAccessPath(user?.role, location.pathname)) {
    return <Navigate to="/unauthorized" replace />;
  }
  return (
    <div className="app-layout">
      <Header />

      <div className="app-layout-body">
        <Sidebar />

        <main className="app-layout-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
