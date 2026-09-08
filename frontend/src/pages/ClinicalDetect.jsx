import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { API } from "../api";
import { useAuth } from "../auth";
import ResultCard from "../components/ResultCard";

const DEFAULTS = {
  diabetes: {
    pregnancies: 3, glucose: 120, blood_pressure: 80, skin_thickness: 22,
    insulin: 100, bmi: 26, diabetes_pedigree: 0.4, age: 40,
  },
  heart: {
    age: 52, sex: 1, cp: 0, trestbps: 130, chol: 220, fbs: 0, restecg: 1,
    thalach: 150, exang: 0, oldpeak: 0.5, slope: 1, ca: 0, thal: 2,
  },
};

export default function ClinicalDetect() {
  const { token } = useAuth();
  const location = useLocation();
  const [modules, setModules] = useState([]);
  const [disease, setDisease] = useState(location.state?.disease || "");
  const [fields, setFields] = useState([]);
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    API.diseases(token).then((list) => {
      const tabular = list.filter((m) => m.type === "tabular");
      setModules(tabular);
      const selected = location.state?.disease || (tabular[0]?.id ?? "");
      setDisease(selected);
      applyModule(tabular.find((m) => m.id === selected)?.fields || []);
    });
  }, [token]);

  function applyModule(flds) {
    setFields(flds || []);
    const next = {};
    for (const f of flds || []) {
      next[f.name] = DEFAULTS[disease]?.[f.name] ?? (f.type === "int" ? 0 : "");
    }
    setValues(next);
  }

  function onDiseaseChange(id) {
    setDisease(id);
    setResult(null);
    const mod = modules.find((m) => m.id === id);
    applyModule(mod?.fields || []);
  }

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const features = {};
      for (const f of fields) {
        features[f.name] = f.type === "int" ? parseInt(values[f.name], 10) : parseFloat(values[f.name]);
      }
      setResult(await API.predictTabular(token, disease, features));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h1>Clinical Data Risk Assessment</h1>
      <form className="card" onSubmit={onSubmit}>
        <label>
          Disease module
          <select value={disease} onChange={(e) => onDiseaseChange(e.target.value)}>
            {modules.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </label>
        <div className="form-grid">
          {fields.map((f) => (
            <label key={f.name}>
              {f.label}
              {f.options ? (
                <select
                  value={values[f.name]}
                  onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
                >
                  {f.options.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              ) : (
                <input
                  type="number"
                  step={f.type === "int" ? 1 : "any"}
                  value={values[f.name]}
                  onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
                />
              )}
            </label>
          ))}
        </div>
        {error && <div className="error">{error}</div>}
        <button className="btn" disabled={busy}>
          {busy ? "Assessing…" : "Assess risk"}
        </button>
      </form>
      {result && <ResultCard prediction={result} />}
    </div>
  );
}