import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { X } from "lucide-react";

import { useAuth } from "../auth/AuthProvider";
import "./Header.css";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  const displayName =
    user?.full_name ||
    user?.username ||
    user?.email ||
    "User";

  const role = user?.role || "USER";

  return (
    <header className="app-header">
      <div className="app-header-left">
        <div className="app-header-brand">
          Email Bomb Detection Platform
        </div>
      </div>

      <div className="app-header-right">
        <div className="header-user-menu">
          <button
            type="button"
            className="header-user-button"
            onClick={() => setIsMenuOpen((current) => !current)}
            aria-expanded={isMenuOpen}
            aria-haspopup="menu"
          >
            <span className="header-user-avatar">
              {displayName.charAt(0).toUpperCase()}
            </span>

            <span className="header-user-info">
              <strong>{displayName}</strong>
              <small>{role}</small>
            </span>

            <span
              className={`header-user-chevron ${
                isMenuOpen ? "is-open" : ""
              }`}
            >
              ▾
            </span>
          </button>

          {isMenuOpen && (
            <div className="header-user-dropdown" role="menu">
              <div className="header-user-dropdown-info">
                <strong>{displayName}</strong>
                <span>{user?.email || ""}</span>
              </div>

              <div className="header-user-dropdown-divider" />

              <button
                type="button"
                className="header-menu-item"
                role="menuitem"
                onClick={() => {
                  setIsMenuOpen(false);
                  setIsProfileOpen(true);
                }}
              >
                Profile
              </button>

              <button
                type="button"
                className="header-menu-item header-menu-item-danger"
                role="menuitem"
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
      {isProfileOpen && (
        <>
          <button
            type="button"
            className="profile-drawer-backdrop"
            aria-label="Close profile panel"
            onClick={() => setIsProfileOpen(false)}
          />
          <aside className="profile-drawer" aria-label="My profile" role="dialog" aria-modal="true">
            <div className="profile-drawer-heading">
              <div>
                <span>ACCOUNT</span>
                <h2>My Profile</h2>
              </div>
              <button type="button" className="profile-drawer-close" aria-label="Close profile" onClick={() => setIsProfileOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="profile-drawer-identity">
              <span className="profile-drawer-avatar">{displayName.charAt(0).toUpperCase()}</span>
              <div><strong>{displayName}</strong><span>{role}</span></div>
            </div>
            <dl className="profile-drawer-details">
              <div><dt>Full name</dt><dd>{user?.full_name || "Not provided"}</dd></div>
              <div><dt>Username</dt><dd>{user?.username || "Not provided"}</dd></div>
              <div><dt>Email</dt><dd>{user?.email || "Not provided"}</dd></div>
              <div><dt>Role</dt><dd>{role}</dd></div>
              <div><dt>Account status</dt><dd>{user?.is_active === false ? "Disabled" : "Active"}</dd></div>
            </dl>
          </aside>
        </>
      )}
    </header>
  );
}
