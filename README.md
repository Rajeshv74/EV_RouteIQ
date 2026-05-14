# ⚡ EV RouteIQ — Deep Learning Road Surface Classification with Integrated Rolling Resistance

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" />
  <img src="https://img.shields.io/badge/Framework-Flask-black?logo=flask" />
  <img src="https://img.shields.io/badge/Model-ResNet50%20%7C%20EfficientNet--B4-orange?logo=pytorch" />
  <img src="https://img.shields.io/badge/Classes-27%20Road%20Surfaces-green" />
  <img src="https://img.shields.io/badge/Physics-SAE%20J2452%20%7C%20ISO%2028580-purple" />
</p>

---

## 📌 What is RouteIQ?

**RouteIQ = Route Intelligence Quotient**

A system that measures the "intelligence" of an EV route — analysing road surface quality, rolling resistance, energy efficiency, and safety to help EV drivers and fleet operators make smarter route decisions.

---

## 🧠 Project Overview

**EV RouteIQ** is a full-stack AI-powered web application that:

1. **Classifies road surfaces** from images using a deep learning model (ResNet50 / EfficientNet-B4) trained on the RSCD dataset (27 classes)
2. **Calculates rolling resistance** (Crr) using real physics standards (SAE J2452, ISO 28580, NRC Canada, Wong 1993)
3. **Estimates EV energy consumption** (kWh) for any road surface + vehicle combination
4. **Compares two routes** to find the most energy-efficient path
5. **Analyses fleet routes** across multiple road image segments
6. **Maps road conditions** geographically on an interactive India map

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Frontend)                    │
│  HTML + Vanilla CSS + JavaScript + Chart.js + Leaflet   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP REST API
┌────────────────────▼────────────────────────────────────┐
│                Flask Backend (app.py)                    │
│  /predict  /compare  /fleet  /heatmap  /geocode         │
└──────┬─────────────┬──────────────┬──────────────┬──────┘
       │             │              │              │
  ResNet50      Physics        EV Database    Weather
  /Effnet-B4    Engine         (ev_database)  Service
  (PyTorch)     (SAE J2452)    12 EVs         Open-Meteo
```

---

## 🗂️ Project Structure

```
mini_project/
├── app.py                    # Flask backend — all API endpoints
├── physics_engine.py         # Rolling resistance & energy physics (SAE/ISO)
├── ev_database.py            # 12 EV vehicle specs database
├── weather_service.py        # Live weather via Open-Meteo API
├── pdf_report.py             # PDF report generator (ReportLab)
├── ev_routeiq_training.py    # Model training script (EfficientNet-B4)
├── validate_model.py         # Model validation on synthetic textures
├── best_model_rscd.pth       # Trained ResNet50 weights (~94 MB)
├── requirements.txt          # Python dependencies
├── procfile                  # Gunicorn config (deployment)
├── tests/
│   └── test_project.py       # Comprehensive test suite (pytest)
├── static/
│   ├── script.js             # All frontend logic
│   └── styles.css            # Dark-mode UI styles
└── templates/
    └── index.html            # Single-page application template
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/UdayKumarM123/MINI_PROJECT_RouteIQ.git
cd MINI_PROJECT_RouteIQ
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python app.py
```

Open browser → **http://127.0.0.1:5001**

---

## 🎯 Features & Tabs

### Tab 1 — 🔍 Classify
- Upload any road image (or use webcam)
- AI classifies into 1 of 27 road surface classes
- Shows: Crr value, kWh/km, estimated range, quality score (0–100), safety level
- Weather auto-fetched for your location
- Download PDF report

### Tab 2 — ⚡ Compare Routes
- Define Route A & Route B (multiple segments each)
- Select EV, speed, temperature, tire pressure, weather
- Compares total energy consumption → declares winner
- Bar chart shows energy difference visually

### Tab 3 — 🚛 Fleet Route Analysis
- Upload up to 10 road images (one per segment)
- AI classifies each segment independently
- Returns total kWh, per-segment breakdown, safety summary

### Tab 4 — 🗺️ Road Condition Heatmap
- Search any Indian city → auto-fills GPS coordinates
- Upload road image → AI classifies it
- Colored dot plotted on OpenStreetMap:
  - 🟢 Green = High quality (safe)
  - 🟡 Yellow = Medium quality
  - 🔴 Red = Low quality / dangerous
- Builds a crowd-sourced road condition database

---

## 🛣️ 27 Road Surface Classes

| Category | Conditions |
|----------|-----------|
| **Dry Asphalt** | Smooth / Slight damage / Severe damage |
| **Dry Concrete** | Smooth / Slight / Severe |
| **Dry** | Gravel / Mud |
| **Wet Asphalt** | Smooth / Slight / Severe |
| **Wet Concrete** | Smooth / Slight / Severe |
| **Wet** | Gravel / Mud |
| **Water Asphalt** | Smooth / Slight / Severe |
| **Water Concrete** | Smooth / Slight / Severe |
| **Water** | Gravel / Mud |
| **Winter** | Fresh Snow / Ice / Melted Snow |

---

## ⚙️ Physics Engine

Rolling resistance energy calculated using real engineering standards:

```
adjusted_Crr = base_Crr × speed_factor × temp_factor × pressure_factor × weather_multiplier

F_rolling = Crr × mass_kg × 9.81          (Newtons)
F_aero    = 0.5 × 0.28 × 2.4 × 1.225 × v²  (Newtons, Cd=0.28)
E_kWh     = (F_rolling + F_aero) × distance_m ÷ 3,600,000
```

**Standards used:**
- Speed factor: SAE J2452
- Temperature factor: NRC Canada rubber stiffness model
- Tire pressure: ISO 28580
- Weather: Wong (1993) automotive engineering tables

---

## 🚗 Supported Vehicles (12 EVs)

| Vehicle | Battery | Range |
|---------|---------|-------|
| Tesla Model 3 LR | 82 kWh | 602 km |
| Tesla Model 3 SR | 57.5 kWh | 438 km |
| Tata Nexon EV | 40.5 kWh | 465 km |
| Tata Tiago EV | 24 kWh | 315 km |
| MG ZS EV | 50.3 kWh | 461 km |
| Hyundai Kona EV | 39.2 kWh | 452 km |
| Kia EV6 | 77.4 kWh | 528 km |
| Mahindra XEV 9e | 79 kWh | 656 km |
| BYD Atto 3 | 60.5 kWh | 521 km |
| Ola S1 Pro | 3.97 kWh | 181 km |
| Ather 450X | 2.9 kWh | 146 km |
| Chetak Electric | 3.2 kWh | 126 km |

---

## 🧪 Running Tests

```bash
# Make sure server is running first: python app.py
pytest tests/test_project.py -v
```

**Test categories:**
- `TestPhysicsEngine` — 16 unit tests for Crr & energy formulas
- `TestEVDatabase` — 4 unit tests for vehicle database
- `TestAPIEndpoints` — 15 integration/API tests (requires server)
- `TestCrrPhysicsCorrectness` — 4 functional tests for physics accuracy

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict` | Classify road image → full EV analysis |
| POST | `/compare` | Compare Route A vs Route B energy |
| POST | `/fleet` | Multi-image fleet route analysis |
| POST | `/heatmap/add` | Add road reading to map |
| GET | `/heatmap/data` | Get all map readings |
| GET | `/geocode?city=X` | City name → lat/lon (India) |
| GET | `/weather?city=X` | Live weather for city |
| GET | `/vehicles` | List all 12 EV specs |
| GET | `/surfaces` | List all 27 surface classes |
| GET | `/health` | Server & model status |
| POST | `/report` | Generate PDF report |

---

## 🏋️ Model Details

| Property | Value |
|----------|-------|
| Primary Model | EfficientNet-B4 (if available) |
| Fallback Model | ResNet50 |
| Dataset | RSCD (Road Surface Condition Dataset) |
| Classes | 27 road surface types |
| Image Size | 224×224 (ResNet50) / 380×380 (EfficientNet) |
| Training Accuracy | ~86.7% (30 epochs) |
| Weights File | `best_model_rscd.pth` (~94 MB) |

---

## 🌤️ External APIs Used

| API | Purpose | Cost |
|-----|---------|------|
| Open-Meteo | Live weather | Free |
| Open-Meteo Geocoding | City → lat/lon | Free |
| OpenStreetMap / Leaflet | Map tiles | Free |

---

## 👥 Team

**Project:** Deep Learning Based Road Surface Classification with Integrated Rolling Resistance

**Repository:** [UdayKumarM123/MINI_PROJECT_RouteIQ](https://github.com/UdayKumarM123/MINI_PROJECT_RouteIQ)

---

## 📄 License

This project is for academic purposes. See individual library licenses for dependencies.
