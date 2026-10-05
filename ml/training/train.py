"""
BharatRoad Twin - Fine-Tuning Script for YOLOv8 Road Damage Detector
=====================================================================
Fine-tunes YOLOv8n/YOLOv8s model on Indian road condition dataset.
Supports CUDA acceleration or CPU fallback.
"""

import sys
import argparse
from pathlib import Path


def train_yolo(data_yaml: str, model_type: str = "yolov8n.pt", epochs: int = 50, batch_size: int = 16, img_size: int = 640):
    """Fine-tunes YOLOv8 model using Ultralytics library if installed."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[WARNING] ultralytics package is not installed. To train, run: pip install ultralytics")
        print("Demo fallback mode active. Mock training session finished.")
        return None

    print(f"Loading pretrained model: {model_type}")
    model = YOLO(model_type)

    print(f"Starting training on dataset: {data_yaml}")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        name="bharatroad_yolov8_damage",
        project="runs/detect",
        exist_ok=True
    )

    print(f"Training completed! Results saved in runs/detect/bharatroad_yolov8_damage")
    return results


def main():
    parser = argparse.ArgumentParser(description="BharatRoad Twin YOLOv8 Damage Detector Fine-Tuning")
    parser.add_argument("--data", type=str, default="dataset/data.yaml", help="Path to dataset data.yaml")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Pretrained weights: yolov8n.pt / yolov8s.pt")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")

    args = parser.parse_args()
    train_yolo(args.data, args.model, args.epochs, args.batch, args.imgsz)


if __name__ == "__main__":
    main()
