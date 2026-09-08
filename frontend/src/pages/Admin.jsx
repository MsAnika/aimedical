import { useEffect, useState } from "react";
import { API } from "../api";
import { useAuth } from "../auth";

export default function Admin() {
  const { token, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    API.adminStats(token)
      .then(setStats)
      .catch((err) => setError(err.message));
  }, [token]);

  if (user?.role !== "admin") return <p className="container">Admins only.</p>;

  return (
    <div className="container">
      <h1>Admin Analytics</h1>
      {error && <div className="error">{error}</div>}
      {stats && (
        <>
          <div className="grid">
            <div className="card stat"><h3>{stats.users}</h3><p>Users</p></div>
            <div className="card stat"><h3>{stats.predictions}</h3><p>Predictions</p></div>
            <div className="card stat"><h3>{stats.reports}</h3><p>Reports</p></div>
            <div className="card stat"><h3>{stats.demo_predictions}</h3><p>Demo predictions</p></div>
          </div>
          <section>
            <h2>Users by role</h2>
            <div className="card">
              {Object.entries(stats.by_role).map(([k, v]) => (
                <div key={k} className="prob-row"><span>{k}</span><span>{v}</span></div>
              ))}
            </div>
          </section>
          <section>
            <h2>Predictions by disease</h2>
            <div className="card">
              {Object.entries(stats.by_disease).map(([k, v]) => (
                <div key={k} className="prob-row"><span>{k}</span><span>{v}</span></div>
              ))}
            </div>
          </section>
          <section>
            <h2>Registered model versions</h2>
            <div className="card">
              {stats.model_versions.length === 0 && <p className="muted">No models registered yet.</p>}
              {stats.model_versions.map((m) => (
                <div key={m.id} className="history-item">
                  <div>
                    <strong>{m.disease}</strong> · {m.version}
                    {m.metrics && <span className="muted"> · acc {m.metrics.accuracy?.toFixed(3)}</span>}
                  </div>
                  <span className="muted">{new Date(m.created_at).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}