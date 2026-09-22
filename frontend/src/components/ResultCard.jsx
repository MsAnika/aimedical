import { useState } from "react";
import { API, downloadUrl } from "../api";
import { useAuth } from "../auth";

export default function ResultCard({ prediction }) {
  const { token } = useAuth();
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const positive = prediction.confidence >= 0.5;

  async function generateReport() {
    setGenerating(true);
    setError("");
    try {
      const res = await API.createReport(token, prediction.id);
      await downloadUrl(res.download_url, token);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="card result">
      <div className="result-header">
        <h2>Prediction: {prediction.label}</h2>
        {prediction.is_demo && <span className="badge badge-demo">DEMO</span>}
        {prediction.report_url && (
          <button className="btn btn-small" onClick={async () => {
            setError("");
            try {
              await downloadUrl(prediction.report_url, token);
            } catch (err) {
              setError(err.message);
            }
          }}>
            Download report
          </button>
        )}
      </div>
      <div className="confidence">
        <div className="bar">
          <div
            className={positive ? "bar-fill bar-high" : "bar-fill bar-low"}
            style={{ width: `${Math.round(prediction.confidence * 100)}%` }}
          />
        </div>
        <span>{Math.round(prediction.confidence * 100)}% confidence</span>
      </div>
      <div className="probs">
        {Object.entries(prediction.probabilities || {}).map(([label, value]) => (
          <div key={label} className="prob-row">
            <span>{label}</span>
            <span>{Math.round(value * 100)}%</span>
          </div>
        ))}
      </div>
      {prediction.heatmap_url && (
        <div className="images">
          {prediction.input_image_url && (
            <figure>
              <img src={prediction.input_image_url} alt="input" />
              <figcaption>Input</figcaption>
            </figure>
          )}
          <figure>
            <img src={prediction.heatmap_url} alt="heatmap" />
            <figcaption>{prediction.is_demo ? "Synthetic demo visualization" : "Grad-CAM model explanation"}</figcaption>
          </figure>
        </div>
      )}
      {prediction.explanation?.note && <p className="muted note">{prediction.explanation.note}</p>}
      <div className="meta">
        <span>Model: {prediction.model_version}</span>
        <span>{new Date(prediction.created_at).toLocaleString()}</span>
      </div>
      {!prediction.report_url && (
        <button className="btn" onClick={generateReport} disabled={generating}>
          {generating ? "Generating…" : "Generate PDF report"}
        </button>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}