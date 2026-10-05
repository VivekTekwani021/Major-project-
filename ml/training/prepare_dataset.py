"""
BharatRoad Twin - ML Dataset Preparation Module
================================================
Converts annotated road surface damage datasets (Pothole, Crack, Damaged Patch)
into standard YOLOv8 directory structure and exports `data.yaml`.
"""

import os
import shutil
import yaml
from pathlib import Path

CLASSES = ["pothole", "crack", "damaged_patch", "unpaved_patch"]


def create_yolo_dataset_structure(base_dir: str = "dataset"):
    """Creates the standard directory layout for training YOLOv8."""
    base = Path(base_dir)
    for split in ["train", "val", "test"]:
        (base / "images" / split).mkdir(parents=True, exist_ok=True)
        (base / "labels" / split).mkdir(parents=True, exist_ok=True)

    yaml_content = {
        "path": str(base.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {i: name for i, name in enumerate(CLASSES)}
    }

    yaml_path = base / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, default_flow_style=False)

    print(f"Dataset directory structure created at: {base}")
    print(f"YAML configuration written to: {yaml_path}")
    return yaml_path


if __name__ == "__main__":
    create_yolo_dataset_structure()
