import { useEffect, useState } from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import { useAuth } from "../../../core/auth/AuthProvider";
import {
  changeUserRole,
  createUser,
  getUser,
  updateUser,
} from "../services/userService";
import {
  EMPTY_USER_FORM,
  ROLE_LABELS,
  USER_ROLES,
} from "../types";

import "./UserForm.css";

function validateForm(form, mode) {
  const errors = {};

  if (!form.full_name.trim()) {
    errors.full_name = "Full name is required.";
  }

  if (!form.username.trim()) {
    errors.username = "Username is required.";
  }

  if (!form.email.trim()) {
    errors.email = "Email is required.";
  }

  if (!form.role) {
    errors.role = "Role is required.";
  }

  if (mode === "create" && !form.password) {
    errors.password = "Password is required.";
  }

  if (
    form.password &&
    form.password.length < 12
  ) {
    errors.password =
      "Password must contain at least 12 characters.";
  }

  return errors;
}

function extractUser(response) {
  if (!response) {
    return null;
  }

  if (
    response.data &&
    typeof response.data === "object" &&
    !Array.isArray(response.data)
  ) {
    return response.data;
  }

  if (
    response.user &&
    typeof response.user === "object"
  ) {
    return response.user;
  }

  if (
    response.result &&
    typeof response.result === "object"
  ) {
    return response.result;
  }

  return response;
}

function buildFormFromUser(user) {
  return {
    email: user?.email ?? "",
    username: user?.username ?? "",
    full_name: user?.full_name ?? "",
    password: "",
    role:
      user?.role ?? USER_ROLES.VIEWER,
  };
}

export default function UserForm({
  mode = "create",
  userId: userIdProp = null,
}) {
  const navigate = useNavigate();
  const { userId: routeUserId } = useParams();
  const { accessToken } = useAuth();

  const userId =
    userIdProp || routeUserId || null;

  const isEdit = mode === "edit";

  const [form, setForm] = useState({
    ...EMPTY_USER_FORM,
  });

  const [originalRole, setOriginalRole] =
    useState(USER_ROLES.VIEWER);

  const [errors, setErrors] = useState({});
  const [serverError, setServerError] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(isEdit);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadUser() {
      if (!isEdit) {
        setIsLoading(false);
        return;
      }

      if (!userId) {
        setIsLoading(false);
        setServerError(
          "User ID is missing.",
        );
        return;
      }

      if (!accessToken) {
        setIsLoading(false);
        setServerError(
          "Authentication is required. Please sign in again.",
        );
        return;
      }

      setIsLoading(true);
      setServerError("");
      setErrors({});

      try {
        const response = await getUser(
          accessToken,
          userId,
        );

        if (!isMounted) {
          return;
        }

        const user =
          extractUser(response);

        if (!user) {
          throw new Error(
            "No user data was returned by the server.",
          );
        }

        const userForm =
          buildFormFromUser(user);

        setForm(userForm);

        setOriginalRole(
          userForm.role,
        );
      } catch (error) {
        if (!isMounted) {
          return;
        }

        console.error(
          "Failed to load user:",
          error,
        );

        setServerError(
          error?.message ||
            "Unable to load the selected user.",
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadUser();

    return () => {
      isMounted = false;
    };
  }, [
    accessToken,
    isEdit,
    userId,
  ]);

  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setErrors((current) => ({
      ...current,
      [name]: "",
    }));

    setServerError("");
  }

  function handleCancel() {
    if (isEdit && userId) {
      navigate(`/users/${userId}`);
      return;
    }

    navigate("/users");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const validationErrors =
      validateForm(form, mode);

    setErrors(validationErrors);

    if (
      Object.keys(validationErrors)
        .length > 0
    ) {
      return;
    }

    if (!accessToken) {
      setServerError(
        "Your session has expired. Please sign in again.",
      );
      return;
    }

    if (isEdit && !userId) {
      setServerError(
        "User ID is missing.",
      );
      return;
    }

    setIsSubmitting(true);
    setServerError("");

    try {
      if (isEdit) {
        /*
         * --------------------------------------------------
         * STEP 1
         * Update normal user account information.
         *
         * Role is intentionally excluded here because
         * role changes have a dedicated backend endpoint
         * and dedicated RBAC permission.
         * --------------------------------------------------
         */

        const updatePayload = {
          email: form.email.trim(),
          username: form.username.trim(),
          full_name:
            form.full_name.trim(),
        };

        await updateUser(
          accessToken,
          userId,
          updatePayload,
        );

        /*
         * --------------------------------------------------
         * STEP 2
         * Change role only when the role actually changed.
         *
         * Backend endpoint:
         *
         * PATCH /users/{user_id}/role
         *
         * This endpoint uses the dedicated
         * USERS_ROLE_CHANGE permission.
         * --------------------------------------------------
         */

        if (
          form.role !== originalRole
        ) {
          await changeUserRole(
            accessToken,
            userId,
            form.role,
          );
        }

        /*
         * Everything succeeded.
         * Return to the user details page.
         */
        navigate(
          `/users/${userId}`,
          {
            replace: true,
          },
        );

        return;
      }

      /*
       * --------------------------------------------------
       * CREATE USER
       * --------------------------------------------------
       */

      await createUser(
        accessToken,
        {
          email: form.email.trim(),
          username:
            form.username.trim(),
          full_name:
            form.full_name.trim(),
          password: form.password,
          role: form.role,
        },
      );

      navigate("/users", {
        replace: true,
      });
    } catch (error) {
      console.error(
        "Failed to save user:",
        error,
      );

      setServerError(
        error?.message ||
          `Unable to ${
            isEdit
              ? "update"
              : "create"
          } user.`,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <main className="user-form-page">
        <div className="user-form-state">
          <div className="loading-spinner" />

          <div>
            <strong>
              Loading user...
            </strong>

            <p>
              Fetching the selected
              user's account information.
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="user-form-page">
      <div className="user-form-container">
        <header className="user-form-header">
          <div>
            <button
              type="button"
              className="back-button"
              onClick={handleCancel}
              disabled={
                isSubmitting
              }
            >
              ← Back
            </button>

            <span className="users-eyebrow">
              User Management
            </span>

            <h1>
              {isEdit
                ? "Edit User"
                : "Create User"}
            </h1>

            <p>
              {isEdit
                ? "Update the user's account information and role."
                : "Create a new platform user account."}
            </p>
          </div>
        </header>

        <section className="user-form-card">
          {serverError && (
            <div
              className="user-form-error"
              role="alert"
            >
              {serverError}
            </div>
          )}

          <form
            className="user-form"
            onSubmit={handleSubmit}
            noValidate
          >
            <div className="user-form-grid">
              <div className="form-field">
                <label htmlFor="full_name">
                  Full Name
                </label>

                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  value={
                    form.full_name
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="John Doe"
                  autoComplete="name"
                  disabled={
                    isSubmitting
                  }
                  aria-invalid={Boolean(
                    errors.full_name,
                  )}
                />

                {errors.full_name && (
                  <span className="field-error">
                    {
                      errors.full_name
                    }
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="username">
                  Username
                </label>

                <input
                  id="username"
                  name="username"
                  type="text"
                  value={
                    form.username
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="john.doe"
                  autoComplete="username"
                  disabled={
                    isSubmitting
                  }
                  aria-invalid={Boolean(
                    errors.username,
                  )}
                />

                {errors.username && (
                  <span className="field-error">
                    {
                      errors.username
                    }
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="email">
                  Email
                </label>

                <input
                  id="email"
                  name="email"
                  type="email"
                  value={
                    form.email
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="john@example.com"
                  autoComplete="email"
                  disabled={
                    isSubmitting
                  }
                  aria-invalid={Boolean(
                    errors.email,
                  )}
                />

                {errors.email && (
                  <span className="field-error">
                    {errors.email}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="role">
                  Role
                </label>

                <select
                  id="role"
                  name="role"
                  value={
                    form.role
                  }
                  onChange={
                    handleChange
                  }
                  disabled={
                    isSubmitting
                  }
                  aria-invalid={Boolean(
                    errors.role,
                  )}
                >
                  {Object.values(
                    USER_ROLES,
                  ).map(
                    (role) => (
                      <option
                        key={role}
                        value={role}
                      >
                        {
                          ROLE_LABELS[
                            role
                          ]
                        }
                      </option>
                    ),
                  )}
                </select>

                {errors.role && (
                  <span className="field-error">
                    {errors.role}
                  </span>
                )}
              </div>

              {!isEdit && <div className="form-field form-field-full">
                <label htmlFor="password">Password</label>
                <input id="password" name="password" type="password" value={form.password} onChange={handleChange} placeholder="Enter a secure password" autoComplete="new-password" disabled={isSubmitting} aria-invalid={Boolean(errors.password)} />
                {errors.password && <span className="field-error">{errors.password}</span>}
                <small>Password must meet the platform security policy.</small>
              </div>}
            </div>

            <div className="user-form-actions">
              <button
                type="button"
                className="secondary-button"
                disabled={
                  isSubmitting
                }
                onClick={
                  handleCancel
                }
              >
                Cancel
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={
                  isSubmitting
                }
              >
                {isSubmitting
                  ? isEdit
                    ? "Saving..."
                    : "Creating..."
                  : isEdit
                    ? "Save Changes"
                    : "Create User"}
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}