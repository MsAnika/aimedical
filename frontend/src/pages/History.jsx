import { useEffect, useState } from "react";
import { API } from "../api";
import { useAuth } from "../auth";
import ResultCard from "../components/ResultCard";

export default function History() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    API.history(token)
      .then((data) => setItems(data.items))
      .catch((err) => setError(err.message));
  }, [token]);

  async function open(id) {
    try {
      setSelected(await API.prediction(token, id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <h1>Screening History</h1>
      {error && <div className="error">{error}</div>}
      {items.length === 0 && <p className="muted">No screenings yet.</p>}
      <div className="history-list">
        {items.map((p) => (
          <div key={p.id} className="card history-item">
            <div>
              <strong>{p.label}</strong>
              <span className="muted"> · {p.disease} · {Math.round(p.confidence * 100)}%</span>
            </div>
            <span className="muted">{new Date(p.created_at).toLocaleString()}</span>
            <button className="btn btn-small" onClick={() => open(p.id)}>View</button>
          </div>
        ))}
      </div>
      {selected && (
        <div className="overlay" onClick={() => setSelected(null)}>
          <div className="overlay-inner" onClick={(e) => e.stopPropagation()}>
            <ResultCard prediction={selected} />
            <button className="btn" onClick={() => setSelected(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}