import { useNavigate } from "react-router-dom";

import "./Unauthorized.css";

export default function Unauthorized() {
  const navigate = useNavigate();

  return (
    <main className="unauthorized-page">
      <div className="unauthorized-card">
        <span className="unauthorized-code">
          403
        </span>

        <h1>
          Access Denied
        </h1>

        <p>
          You do not have permission
          to access this page.
        </p>

        <button
          type="button"
          onClick={() =>
            navigate("/")
          }
        >
          Back to Dashboard
        </button>
      </div>
    </main>
  );
}