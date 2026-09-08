from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DiseaseField(BaseModel):
    name: str
    label: str
    type: str
    required: bool = True
    options: list[str] | None = None


class DiseaseModule(BaseModel):
    id: str
    name: str
    type: str
    description: str
    fields: list[DiseaseField] | None = None
    classes: list[str] | None = None
    model_status: str
    model_version: str | None = None


class ImagePredictionIn(BaseModel):
    disease: str


class TabularPredictionIn(BaseModel):
    disease: str
    features: dict[str, Any]


class PredictionOut(BaseModel):
    id: int
    disease: str
    input_type: str
    label: str
    confidence: float
    probabilities: dict | None
    explanation: dict | None
    model_version: str
    is_demo: bool
    created_at: datetime
    input_image_url: str | None = None
    heatmap_url: str | None = None
    report_url: str | None = None

    model_config = {"from_attributes": True}


class HistoryOut(BaseModel):
    total: int
    items: list[PredictionOut]


class ReportOut(BaseModel):
    detail: str
    report_id: int
    download_url: str


class AdminStats(BaseModel):
    users: int
    predictions: int
    by_role: dict[str, int]
    by_disease: dict[str, int]
    demo_predictions: int
    model_versions: list[dict[str, Any]]
