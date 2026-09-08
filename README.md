# AI-Based Medical Diagnostic System

Final semester project: an AI decision-support platform for disease detection from medical images
and structured clinical data, with explainability (Grad-CAM / SHAP), role-based access, and PDF reports.

> **Scope disclaimer:** This is an academic decision-support prototype for screening and demonstration.
> It is NOT a certified diagnostic device and does not replace evaluation by a licensed medical professional.

## Architecture

- **Frontend:** React.js + Vite (patient / doctor dashboards)
- **Backend API:** FastAPI + SQLAlchemy, JWT authentication
- **ML inference:** PyTorch (ResNet/EfficientNet, transfer learning) for images; scikit-learn/XGBoost for tabular data
- **Explainability:** Grad-CAM (images), SHAP (tabular features)
- **Data:** SQLite (dev) / PostgreSQL (docker); file storage for uploaded images + generated PDFs

## Disease modules

| Module | Type | Model | Explanation |
|--------|------|-------|-------------|
| Pneumonia (chest X-ray) | Image (binary) | CNN, transfer learning | Grad-CAM |
| Skin lesion (cancer) | Image (multi-class, 7) | CNN, transfer learning | Grad-CAM |
| Diabetes | Tabular (binary) | Random Forest / XGBoost | SHAP |
| Heart disease | Tabular (binary) | Random Forest / XGBoost | SHAP |

## Quick start (local, no ML deps)

From the project root, install the dependencies once:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
```

Then start both development servers with one command:

```powershell
.\start.ps1
```

This starts the API at http://localhost:8000/docs and the frontend at http://localhost:5173. No frontend build is required.

To start them manually instead:

```powershell
# Backend (run from the project root)
python -m uvicorn app.main:app --app-dir backend --reload --port 8000

# Frontend (separate terminal, from the project root)
cd frontend
npm run dev
```

Without trained model files, the API runs in **demo mode**: predictors return plausible,
clearly-labeled demo results so the whole flow is testable. Train real models with the
pipeline below to replace them.

## Training real models

```powershell
pip install -r backend\requirements-ml.txt

# Download datasets (see each script for requirements; some need Kaggle credentials)
python backend\ml\data\download_diabetes.py
python backend\ml\data\download_heart.py
python backend\ml\data\download_pneumonia.py
python backend\ml\data\download_skin.py

# Train and export models into backend\app\services\ml\models\
python backend\ml\train_tabular.py diabetes
python backend\ml\train_tabular.py heart
python backend\ml\train_image.py pneumonia
python backend\ml\train_image.py skin
```

Dataset sources (see `backend/ml/data/*.py` for URLs and instructions):
- Pneumonia X-rays: Chest X-Ray Images (Pneumonia), Kaggle
- Skin lesions: ISIC / HAM10000 (Kaggle or ISIC archive)
- Diabetes: PIMA Indians Diabetes (OpenML id 37)
- Heart disease: Cleveland / Heart Statlog (UCI, via OpenML)

## Docker

```powershell
docker compose up --build
# frontend http://localhost:5173  backend http://localhost:8000/docs
```

## Project layout

```
backend/
  app/
    api/routes/      # FastAPI endpoints
    core/            # config, db, security, ORM models
    schemas/         # Pydantic request/response models
    services/
      ml/            # model registry, CNN inference, Grad-CAM, SHAP, demo fallbacks
      report.py      # PDF report generation
    main.py
  ml/
    data/            # dataset downloaders
    train_*.py       # training + export scripts
frontend/
  src/pages/         # Login, Register, Dashboard, ImageDetect, ClinicalDetect, History, Report
docs/
```

## API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | - | Create account (patient/doctor/admin) |
| POST | `/api/auth/login` | - | Get JWT |
| GET | `/api/auth/me` | yes | Current user |
| GET | `/api/diseases` | yes | Available modules + input fields |
| POST | `/api/predictions/image` | yes | Image prediction (multipart) |
| POST | `/api/predictions/tabular` | yes | Clinical data prediction |
| GET | `/api/predictions/{id}` | yes | Prediction detail |
| GET | `/api/history` | yes | Own prediction history |
| POST | `/api/predictions/{id}/report` | yes | Generate PDF report |
| GET | `/api/admin/stats` | admin | Usage + model stats |
