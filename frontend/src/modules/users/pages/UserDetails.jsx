import { useEffect, useState } from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import { useAuth } from "../../../core/auth/AuthProvider";
import ErrorNotice from "../../../core/components/ErrorNotice";

import Can from "../../../core/permissions/Can";
import { PERMISSIONS } from "../../../core/permissions/permissions";

import UserStatusBadge from "../components/UserStatusBadge";

import {
  getRoleLabel,
} from "../types";

import {
  disableUser,
  enableUser,
  getUser,
} from "../services/userService";

import "./UserDetails.css";

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}

function DetailItem({
  label,
  value,
}) {
  return (
    <div className="user-detail-item">
      <span>{label}</span>

      <strong>
        {value || "—"}
      </strong>
    </div>
  );
}

export default function UserDetails() {
  const {
    userId,
  } = useParams();

  const navigate = useNavigate();

  const {
    accessToken,
  } = useAuth();

  const [user, setUser] =
    useState(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isStatusUpdating,
    setIsStatusUpdating,
  ] = useState(false);

  const [error, setError] =
    useState("");

  const [
    statusError,
    setStatusError,
  ] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      if (!accessToken) {
        if (!cancelled) {
          setError(
            "Authentication is required. Please sign in again.",
          );

          setIsLoading(false);
        }

        return;
      }

      if (!userId) {
        if (!cancelled) {
          setError(
            "User ID is missing.",
          );

          setIsLoading(false);
        }

        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const response =
          await getUser(
            accessToken,
            userId,
          );

        if (!cancelled) {
          setUser(response);
        }
      } catch (requestError) {
        if (!cancelled) {
          console.error(
            "Failed to load user:",
            requestError,
          );

          setError(
            requestError?.message ||
              "Unable to load user.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadUser();

    return () => {
      cancelled = true;
    };
  }, [
    accessToken,
    userId,
  ]);

  async function handleStatusChange() {
    if (!user || !userId) {
      return;
    }

    if (!accessToken) {
      setStatusError(
        "Your session has expired. Please sign in again.",
      );

      return;
    }

    const currentlyActive =
      Boolean(user.is_active);

    const action =
      currentlyActive
        ? "disable"
        : "enable";

    const actionLabel =
      currentlyActive
        ? "disable"
        : "enable";

    const confirmed =
      window.confirm(
        `Are you sure you want to ${actionLabel} this user?`,
      );

    if (!confirmed) {
      return;
    }

    setIsStatusUpdating(true);
    setStatusError("");

    try {
      const response =
        currentlyActive
          ? await disableUser(
              accessToken,
              userId,
            )
          : await enableUser(
              accessToken,
              userId,
            );

      if (response) {
        setUser(response);
      } else {
        /*
         * Fallback:
         * If the backend does not return
         * the updated user, reload it.
         */
        const refreshedUser =
          await getUser(
            accessToken,
            userId,
          );

        setUser(
          refreshedUser,
        );
      }
    } catch (requestError) {
      console.error(
        `Failed to ${action} user:`,
        requestError,
      );

      setStatusError(
        requestError?.message ||
          `Unable to ${action} user.`,
      );
    } finally {
      setIsStatusUpdating(false);
    }
  }

  function handleBack() {
    navigate("/users");
  }

  function handleEdit() {
    if (!user?.id) {
      return;
    }

    navigate(
      `/users/${user.id}/edit`,
    );
  }

  if (isLoading) {
    return (
      <main className="user-details-page">
        <div className="user-details-state">
          <div className="loading-spinner" />

          <span>
            Loading user...
          </span>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="user-details-page">
        <div className="user-details-error">
          <ErrorNotice title="User details could not be loaded" message={error} />

          <button
            type="button"
            onClick={handleBack}
          >
            Back to Users
          </button>
        </div>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  const isActive =
    Boolean(user.is_active);

  return (
    <main className="user-details-page">
      <div className="user-details-container">
        <header className="user-details-header">
          <div>
            <button
              type="button"
              className="back-button"
              onClick={handleBack}
              disabled={
                isStatusUpdating
              }
            >
              ← Back to Users
            </button>

            <span className="users-eyebrow">
              User Management
            </span>

            <h1>
              User Details
            </h1>

            <p>
              View account information
              and access status.
            </p>
          </div>

          <div className="user-details-header-actions">
            {isActive ? (
              <Can
                permission={
                  PERMISSIONS.USERS_DISABLE
                }
              >
                <button
                  type="button"
                  className="secondary-button"
                  onClick={
                    handleStatusChange
                  }
                  disabled={
                    isStatusUpdating
                  }
                >
                  {isStatusUpdating
                    ? "Updating..."
                    : "Disable User"}
                </button>
              </Can>
            ) : (
              <Can
                permission={
                  PERMISSIONS.USERS_ENABLE
                }
              >
                <button
                  type="button"
                  className="secondary-button"
                  onClick={
                    handleStatusChange
                  }
                  disabled={
                    isStatusUpdating
                  }
                >
                  {isStatusUpdating
                    ? "Updating..."
                    : "Enable User"}
                </button>
              </Can>
            )}

            <Can
              permission={
                PERMISSIONS.USERS_UPDATE
              }
            >
              <button
                type="button"
                className="primary-button"
                onClick={handleEdit}
                disabled={
                  isStatusUpdating
                }
              >
                Edit User
              </button>
            </Can>
          </div>
        </header>

        {statusError && (
          <ErrorNotice className="user-details-action-error" title="Account status could not be changed" message={statusError} />
        )}

        <section className="user-profile-card">
          <div className="user-profile-main">
            <div className="user-profile-avatar">
              {(
                user.full_name ||
                user.username ||
                user.email ||
                "U"
              )
                .charAt(0)
                .toUpperCase()}
            </div>

            <div>
              <h2>
                {user.full_name ||
                  "Unnamed User"}
              </h2>

              <p>
                {user.email}
              </p>

              <div className="user-profile-meta">
                <span>
                  @{user.username}
                </span>

                <span>
                  {getRoleLabel(
                    user.role,
                  )}
                </span>

                <UserStatusBadge
                  user={user}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="user-detail-section">
          <div className="user-detail-section-header">
            <div>
              <h2>
                Account Information
              </h2>

              <p>
                Basic identity and
                account information.
              </p>
            </div>
          </div>

          <div className="user-detail-grid">
            <DetailItem
              label="Full Name"
              value={
                user.full_name
              }
            />

            <DetailItem
              label="Username"
              value={
                user.username
              }
            />

            <DetailItem
              label="Email"
              value={
                user.email
              }
            />

            <DetailItem
              label="Role"
              value={getRoleLabel(
                user.role,
              )}
            />

            <DetailItem
              label="Account Created"
              value={formatDate(
                user.created_at,
              )}
            />

            <DetailItem
              label="Last Updated"
              value={formatDate(
                user.updated_at,
              )}
            />
          </div>
        </section>

        <section className="user-detail-section">
          <div className="user-detail-section-header">
            <div>
              <h2>
                Security Status
              </h2>

              <p>
                Authentication and
                account security state.
              </p>
            </div>
          </div>

          <div className="user-detail-grid">
            <DetailItem
              label="Account Status"
              value={
                isActive
                  ? "Active"
                  : "Disabled"
              }
            />

            <DetailItem
              label="Locked"
              value={
                user.is_locked
                  ? "Yes"
                  : "No"
              }
            />

            <DetailItem
              label="Force Password Change"
              value={
                user.force_password_change
                  ? "Required"
                  : "Not Required"
              }
            />

            <DetailItem
              label="Failed Login Attempts"
              value={String(
                user.failed_login_attempts ??
                  0,
              )}
            />

            <DetailItem
              label="Last Login"
              value={formatDate(
                user.last_login_at,
              )}
            />

            <DetailItem
              label="Locked At"
              value={formatDate(
                user.locked_at,
              )}
            />
          </div>
        </section>
      </div>
    </main>
  );
}
