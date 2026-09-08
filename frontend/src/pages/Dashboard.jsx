import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { API } from "../api";
import { useAuth } from "../auth";

export default function Dashboard() {
  const { user, token } = useAuth();
  const [modules, setModules] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    API.diseases(token)
      .then(setModules)
      .catch((err) => setError(err.message));
  }, [token]);

  const images = modules.filter((m) => m.type === "image");
  const tabular = modules.filter((m) => m.type === "tabular");

  return (
    <div className="container">
      <div className="banner">
        <strong>Good to see you, {user?.full_name}.</strong> Your clinical workspace is ready. Choose a screening pathway below to begin.
      </div>
      {error && <div className="error">{error}</div>}
      <section>
        <h2>Image-based detection</h2>
        <div className="grid">
          {images.map((m) => (
            <div key={m.id} className="card module-card">
              <h3>{m.name}</h3>
              <p className="muted">{m.description}</p>
              <p>
                Status:{" "}
                <span className={`badge ${m.model_status === "loaded" ? "badge-ok" : "badge-demo"}`}>
                  {m.model_status === "loaded" ? "Real model" : "Demo mode"}
                </span>
              </p>
              <Link to="/image" state={{ disease: m.id }} className="btn">
                Run detection
              </Link>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2>Clinical data risk assessment</h2>
        <div className="grid">
          {tabular.map((m) => (
            <div key={m.id} className="card module-card">
              <h3>{m.name}</h3>
              <p className="muted">{m.description}</p>
              <p>
                Status:{" "}
                <span className={`badge ${m.model_status === "loaded" ? "badge-ok" : "badge-demo"}`}>
                  {m.model_status === "loaded" ? "Real model" : "Demo mode"}
                </span>
              </p>
              <Link to="/clinical" state={{ disease: m.id }} className="btn">
                Run assessment
              </Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}