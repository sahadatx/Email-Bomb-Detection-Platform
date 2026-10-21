import { useAuth } from "../../../core/auth/AuthProvider";
import "./ProfilePage.css";

export default function ProfilePage() {
  const { user } = useAuth();
  const name = user?.full_name || user?.username || "User";
  const initials = name.trim().charAt(0).toUpperCase() || "U";

  return (
    <main className="own-profile-page">
      <header className="own-profile-heading">
        <span>ACCOUNT</span>
        <h1>My Profile</h1>
        <p>Your account information.</p>
      </header>

      <section className="own-profile-card" aria-label="Profile details">
        <div className="own-profile-identity">
          <div className="own-profile-avatar" aria-hidden="true">{initials}</div>
          <div>
            <h2>{name}</h2>
            <span>{user?.role || "USER"}</span>
          </div>
        </div>
        <dl className="own-profile-details">
          <div><dt>Full name</dt><dd>{user?.full_name || "Not provided"}</dd></div>
          <div><dt>Username</dt><dd>{user?.username || "Not provided"}</dd></div>
          <div><dt>Email</dt><dd>{user?.email || "Not provided"}</dd></div>
          <div><dt>Role</dt><dd>{user?.role || "Not provided"}</dd></div>
          <div><dt>Account status</dt><dd>{user?.is_active === false ? "Disabled" : "Active"}</dd></div>
        </dl>
      </section>
    </main>
  );
}
