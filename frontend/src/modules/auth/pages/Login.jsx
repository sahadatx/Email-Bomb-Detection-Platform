import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../../core/auth/AuthProvider";
import { getCurrentUser, login as loginRequest } from "../services/authService";
import { LOGIN_INITIAL_VALUES } from "../types";

import "./Login.css";

const DEFAULT_AUTHENTICATED_ROUTE = "/emails";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const { login } = useAuth();

  const [form, setForm] = useState(LOGIN_INITIAL_VALUES);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;

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

  function validate() {
    const nextErrors = {};

    if (!form.email.trim()) {
      nextErrors.email = "Email is required.";
    }

    if (!form.password) {
      nextErrors.password = "Password is required.";
    }

    return nextErrors;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const validationErrors = validate();

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setServerError("");

    try {
      const response = await loginRequest({
        email: form.email.trim(),
        password: form.password,
      });

      // /auth/login intentionally returns only a token. Load the server
      // user record so role-gated navigation and module actions can render.
      const authenticatedUser = response.user ?? await getCurrentUser(response.access_token);

      login({
        accessToken: response.access_token,
        user: authenticatedUser,
      });

      /*
       * If the user was originally sent to the login page from
       * a protected route, preserve that destination.
       *
       * Otherwise, use the Email Security overview as the
       * authenticated application landing page.
       */
      const requestedPath = location.state?.from?.pathname;

      const redirectPath =
        requestedPath &&
        requestedPath !== "/login" &&
        requestedPath !== "/"
          ? requestedPath
          : DEFAULT_AUTHENTICATED_ROUTE;

      navigate(redirectPath, {
        replace: true,
      });
    } catch (error) {
      setServerError(
        error?.message ||
          "Unable to sign in. Please check your credentials.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-header">
          <div className="login-logo">
            EB
          </div>

          <h1>Email Bomb Detection Platform</h1>

          <p>
            Sign in to access the security platform.
          </p>
        </div>

        <form
          className="login-form"
          onSubmit={handleSubmit}
          noValidate
        >
          {serverError && (
            <div
              className="login-error"
              role="alert"
            >
              {serverError}
            </div>
          )}

          <div className="form-field">
            <label htmlFor="email">
              Email
            </label>

            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="admin@example.com"
              autoComplete="email"
              disabled={isSubmitting}
              aria-invalid={Boolean(errors.email)}
            />

            {errors.email && (
              <span className="field-error">
                {errors.email}
              </span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter your password"
              autoComplete="current-password"
              disabled={isSubmitting}
              aria-invalid={Boolean(errors.password)}
            />

            {errors.password && (
              <span className="field-error">
                {errors.password}
              </span>
            )}
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>

        <footer className="login-footer">
          <span>
            Email Bomb Detection Platform
          </span>
        </footer>
      </section>
    </main>
  );
}
