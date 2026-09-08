import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { API } from "../api";
import { useAuth } from "../auth";
import ResultCard from "../components/ResultCard";

export default function ImageDetect() {
  const { token } = useAuth();
  const location = useLocation();
  const [modules, setModules] = useState([]);
  const [disease, setDisease] = useState(location.state?.disease || "");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    API.diseases(token).then((list) => {
      setModules(list.filter((m) => m.type === "image"));
      if (!disease && list.length) setDisease(list.find((m) => m.type === "image").id);
    });
  }, [token]);

  function onFile(e) {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!file || !disease) return;
    setBusy(true);
    setError("");
    try {
      setResult(await API.predictImage(token, disease, file));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h1>Image-Based Disease Detection</h1>
      <form className="card" onSubmit={onSubmit}>
        <label>
          Disease module
          <select value={disease} onChange={(e) => setDisease(e.target.value)}>
            {modules.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </label>
        <label>
          Medical image (X-ray / skin lesion)
          <input type="file" accept="image/*" onChange={onFile} />
        </label>
        {preview && <img src={preview} alt="preview" className="preview" />}
        {error && <div className="error">{error}</div>}
        <button className="btn" disabled={busy || !file}>
          {busy ? "Analyzing…" : "Analyze image"}
        </button>
      </form>
      {result && <ResultCard prediction={result} />}
    </div>
  );
}