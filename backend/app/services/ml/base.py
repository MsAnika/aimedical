from dataclasses import dataclass, field


@dataclass
class FeatureSpec:
    name: str
    label: str
    type: str = "float"
    required: bool = True
    options: list[str] | None = None
    min: float | None = None
    max: float | None = None


@dataclass
class DiseaseSpec:
    id: str
    name: str
    type: str
    description: str
    classes: list[str] = field(default_factory=list)
    features: list[FeatureSpec] = field(default_factory=list)
    model_file: str | None = None
    metadata_file: str | None = None


DISEASES: dict[str, DiseaseSpec] = {
    "pneumonia": DiseaseSpec(
        id="pneumonia",
        name="Pneumonia (Chest X-Ray)",
        type="image",
        description="Detect pneumonia from chest X-ray images.",
        classes=["Normal", "Pneumonia"],
        model_file="pneumonia.pt",
        metadata_file="pneumonia.json",
    ),
    "skin": DiseaseSpec(
        id="skin",
        name="Skin Lesion Classification",
        type="image",
        description="Classify skin lesion images (HAM10000 classes).",
        classes=[
            "Melanocytic nevi",
            "Melanoma",
            "Benign keratosis",
            "Basal cell carcinoma",
            "Actinic keratoses",
            "Vascular lesions",
            "Dermatofibroma",
        ],
        model_file="skin.pt",
        metadata_file="skin.json",
    ),
    "diabetes": DiseaseSpec(
        id="diabetes",
        name="Diabetes Risk",
        type="tabular",
        description="Estimate diabetes risk from clinical parameters (PIMA).",
        classes=["No Diabetes", "Diabetes"],
        features=[
            FeatureSpec("pregnancies", "Pregnancies", "int", True, None, 0, 20),
            FeatureSpec("glucose", "Glucose (mg/dL)", "float", True, None, 0, 300),
            FeatureSpec("blood_pressure", "Blood Pressure (mmHg)", "float", True, None, 0, 200),
            FeatureSpec("skin_thickness", "Skin Thickness (mm)", "float", True, None, 0, 100),
            FeatureSpec("insulin", "Insulin (mu U/ml)", "float", True, None, 0, 900),
            FeatureSpec("bmi", "BMI", "float", True, None, 0, 70),
            FeatureSpec("diabetes_pedigree", "Diabetes Pedigree Function", "float", True, None, 0, 3),
            FeatureSpec("age", "Age", "int", True, None, 1, 120),
        ],
        model_file="diabetes.joblib",
        metadata_file="diabetes.json",
    ),
    "heart": DiseaseSpec(
        id="heart",
        name="Heart Disease Risk",
        type="tabular",
        description="Estimate heart disease risk from clinical parameters (Cleveland).",
        classes=["No Heart Disease", "Heart Disease"],
        features=[
            FeatureSpec("age", "Age", "int", True, None, 1, 120),
            FeatureSpec("sex", "Sex", "int", True, [0, 1], 0, 1),
            FeatureSpec("cp", "Chest Pain Type", "int", True, [0, 1, 2, 3], 0, 3),
            FeatureSpec("trestbps", "Resting Blood Pressure (mmHg)", "float", True, None, 50, 250),
            FeatureSpec("chol", "Serum Cholesterol (mg/dl)", "float", True, None, 100, 600),
            FeatureSpec("fbs", "Fasting Blood Sugar > 120 mg/dl", "int", True, [0, 1], 0, 1),
            FeatureSpec("restecg", "Resting ECG", "int", True, [0, 1, 2], 0, 2),
            FeatureSpec("thalach", "Max Heart Rate", "int", True, None, 60, 220),
            FeatureSpec("exang", "Exercise Induced Angina", "int", True, [0, 1], 0, 1),
            FeatureSpec("oldpeak", "ST Depression", "float", True, None, -5, 10),
            FeatureSpec("slope", "ST Slope", "int", True, [0, 1, 2], 0, 2),
            FeatureSpec("ca", "Major Vessels", "int", True, None, 0, 4),
            FeatureSpec("thal", "Thalassemia", "int", True, [1, 2, 3], 1, 3),
        ],
        model_file="heart.joblib",
        metadata_file="heart.json",
    ),
}
