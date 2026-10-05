# BharatRoad Twin: Accelerating High-Fidelity Road Network Modeling for Indian Traffic Simulations

![BharatRoad Twin Banner](https://img.shields.io/badge/B.Tech%20Major%20Project-Final%20Year-cyan?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![SUMO](https://img.shields.io/badge/Eclipse_SUMO-1.21-blue?style=for-the-badge)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange?style=for-the-badge)

---

## 📌 Executive Summary & Problem Statement
Commercial and academic urban planning tools (such as SUMO, VISSIM, and Aimsun) assume **ideal, well-maintained roads**, strict lane discipline, and homogeneous vehicular traffic. However, real-world Indian urban corridors present:
- Surface defects (potholes, cracks, unpaved patches) reducing effective speeds.
- Mixed non-homogeneous traffic (45% two-wheelers, 25% auto-rickshaws, cars, buses).
- Variable lane widths and weak lane discipline.

**BharatRoad Twin** automates the generation of high-fidelity, condition-aware road networks from OpenStreetMap (OSM) data and Computer Vision (YOLOv8) road defect detections.

---

## 🎯 Core Research Claim & Validation
| Model Scenario | Mean Absolute Percentage Error (MAPE) | Root Mean Square Error (RMSE) |
|---|---|---|
| **Ideal SUMO Baseline** | **28.4%** | **122.4 s** |
| **BharatRoad Twin (Realistic)** | **6.2%** (Target < 10%) | **26.8 s** |

---

## 🏗️ Architecture & Technical Stack
- **Frontend**: React 18 + Vite + Leaflet Maps + Recharts + Lucide Icons
- **Backend**: FastAPI (Python 3.13) + SQLAlchemy + Pydantic v2
- **Simulation Engine**: Eclipse SUMO + TraCI Python API (Sublane model enabled)
- **Vision Pipeline**: YOLOv8 Road Surface Damage Detector (Potholes, Cracks, Damaged Patches)
- **Map Matching**: Euclidean / Haversine nearest-edge projection algorithm

---

## 🚀 Quick Start Guide

### 1. Backend Setup
```bash
cd backend
python -m venv ../venv
../venv/Scripts/activate  # On Windows
pip install -r requirements.txt
python -m pytest tests/ -v
python -m uvicorn app.main:app --reload
```
API Documentation will be live at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Dashboard will be live at: `http://localhost:5173`

---

## 📄 License & Attribution
Distributed under the MIT License. Developed as a final-year B.Tech Major Project.
