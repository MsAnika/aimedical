import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.services.ml.base import DISEASES

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
INPUT_SIZE = 224


def _build_model(arch: str, n_classes: int):
    import torch
    from torchvision import models as tv_models

    if arch == "efficientnet_b0":
        model = tv_models.efficientnet_b0(weights=tv_models.EfficientNet_B0_Weights.DEFAULT)
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, n_classes)
    else:
        model = tv_models.resnet18(weights=tv_models.ResNet18_Weights.DEFAULT)
        model.fc = torch.nn.Linear(model.fc.in_features, n_classes)
    return model


class SkinDataset:
    def __init__(self, images_dir: Path, csv_path: Path, classes: list[str]):
        import pandas as pd
        import torch
        import torchvision.transforms as T

        df = pd.read_csv(csv_path)
        df = df[df["dx"].isin(classes)]
        df = df.drop_duplicates(subset="image_id")
        df = df.reset_index(drop=True)
        self.df = df
        self.images_dir = Path(images_dir)
        self.class_index = {c: i for i, c in enumerate(classes)}
        self.transform = T.Compose(
            [
                T.Resize((INPUT_SIZE, INPUT_SIZE)),
                T.ToTensor(),
                T.Normalize(MEAN, STD),
            ]
        )

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        from PIL import Image

        row = self.df.iloc[idx]
        img = Image.open(self.images_dir / f"{row['image_id']}.jpg").convert("RGB")
        return self.transform(img), self.class_index[row["dx"]]


def _get_loaders(disease: str, data_dir: Path, batch_size: int, seed: int):
    import torch
    from torch.utils.data import DataLoader, random_split
    from torchvision import datasets
    from torchvision.transforms import v2

    spec = DISEASES[disease]
    transform = v2.Compose(
        [
            v2.Resize((INPUT_SIZE, INPUT_SIZE)),
            v2.RandomHorizontalFlip(),
            v2.RandomRotation(10),
            v2.ToTensor(),
            v2.Normalize(MEAN, STD),
        ]
    )
    eval_transform = v2.Compose(
        [
            v2.Resize((INPUT_SIZE, INPUT_SIZE)),
            v2.ToTensor(),
            v2.Normalize(MEAN, STD),
        ]
    )

    if disease == "pneumonia":
        train_dir = data_dir / "pneumonia" / "train"
        test_dir = data_dir / "pneumonia" / "test"
        val_dir = data_dir / "pneumonia" / "val"
        train_ds = datasets.ImageFolder(str(train_dir), transform=transform)
        test_ds = datasets.ImageFolder(str(test_dir), transform=eval_transform) if test_dir.exists() else None
        val_ds = datasets.ImageFolder(str(val_dir), transform=eval_transform) if val_dir.exists() else None
        classes = train_ds.classes
    elif disease == "skin":
        csv_path = data_dir / "skin" / "HAM10000_metadata.csv"
        images_dir = data_dir / "skin" / "images"
        full = SkinDataset(images_dir, csv_path, spec.classes)
        classes = spec.classes
        n_val = max(1, int(0.15 * len(full)))
        n_test = max(1, int(0.15 * len(full)))
        n_train = len(full) - n_val - n_test
        gen = torch.Generator().manual_seed(seed)
        train_ds, val_ds, test_ds = random_split(full, [n_train, n_val, n_test], generator=gen)
        train_ds.dataset.transform = transform
    else:
        sys.exit(f"Unsupported disease {disease}")

    def dl(ds):
        return DataLoader(ds, batch_size=batch_size, shuffle=bool(ds is train_ds), num_workers=0) if ds is not None else None

    return dl(train_ds), dl(val_ds), dl(test_ds), classes


def _evaluate(model, loader, device):
    import torch

    model.eval()
    y_true, y_prob, y_pred = [], [], []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            probs = torch.softmax(model(x), dim=1)
            y_prob.extend(probs[:, 1].tolist() if probs.shape[1] == 2 else probs.max(dim=1).values.tolist())
            y_pred.extend(probs.argmax(dim=1).tolist())
            y_true.extend(y.tolist())
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train image CNN (pneumonia / skin)")
    parser.add_argument("disease", choices=["pneumonia", "skin"])
    parser.add_argument("--data-dir", type=Path, default=Path("backend/ml/data"))
    parser.add_argument("--arch", choices=["resnet18", "efficientnet_b0"], default="resnet18")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--register", action="store_true", help="Record model version in the app database")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    import torch

    spec = DISEASES[args.disease]
    out_dir = args.out or Path(get_settings().model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    train_loader, val_loader, test_loader, classes = _get_loaders(
        args.disease, args.data_dir, args.batch_size, args.seed
    )
    if val_loader is None:
        val_loader = test_loader
    if train_loader is None:
        sys.exit("No training data found. Run the download script first.")
    if len(classes) != len(spec.classes):
        print(f"Warning: dataset classes {classes} differ from spec {spec.classes}")

    model = _build_model(args.arch, len(classes)).to(device)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    print("Epoch | Progress | Loss   | Val Acc | Time")
    print("------|----------|--------|---------|------")
    for epoch in range(1, args.epochs + 1):
        epoch_started = time.perf_counter()
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(x)
        scheduler.step()
        val_metrics = _evaluate(model, val_loader, device)
        print(
            f"{epoch:>5}/{args.epochs:<5} | {epoch / args.epochs:>7.0%}  | "
            f"{total_loss / max(len(train_loader.dataset), 1):.4f} | "
            f"{val_metrics['accuracy']:.4f}  | {time.perf_counter() - epoch_started:.1f}s",
            flush=True,
        )

    metrics = _evaluate(model, test_loader if test_loader is not None else val_loader, device)
    print(json.dumps(metrics, indent=2))

    model_path = out_dir / spec.model_file
    metadata_path = out_dir / spec.metadata_file
    torch.save(model.state_dict(), model_path)
    metadata_path.write_text(
        json.dumps(
            {
                "classes": spec.classes,
                "arch": args.arch,
                "input_size": INPUT_SIZE,
                "mean": MEAN,
                "std": STD,
                "metrics": metrics,
            },
            indent=2,
        ),
        "utf-8",
    )
    print(f"Saved model to {model_path}")
    print(f"Saved metadata to {metadata_path}")

    if args.register:
        from app.core.database import SessionLocal
        from app.core.models import ModelVersion

        with SessionLocal() as session:
            session.add(
                ModelVersion(
                    disease=args.disease,
                    version=f"{args.arch}-{model_path.stem}",
                    metrics=metrics,
                )
            )
            session.commit()
        print("Registered model version in database")


if __name__ == "__main__":
    main()