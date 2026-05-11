# 🌫️ AQI Predictor — Federal Air Quality ML Project

Predict next-day Air Quality Index (AQI) using EPA AirNow data + NOAA weather features.

---

## Project Structure

```
aqi_predictor/
├── notebooks/
│   ├── 01_data_collection.ipynb   # Pull & save data from APIs
│   ├── 02_eda.ipynb               # Explore, clean, visualize
│   └── 03_model.ipynb             # Train & evaluate ML models
├── data/
│   ├── raw/                       # Raw API responses (CSV)
│   └── processed/                 # Cleaned, feature-engineered data
├── models/                        # Saved model files (.pkl)
├── utils/
│   ├── airnow.py                  # AirNow API helpers
│   └── noaa.py                    # NOAA weather API helpers
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Free API Keys

| API | Sign Up | Notes |
|-----|---------|-------|
| **AirNow** | https://docs.airnowapi.org/ | Free, instant |
| **NOAA CDO** | https://www.ncdc.noaa.gov/cdo-web/token | Free, email token |

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export AIRNOW_API_KEY="your-key-here"
export NOAA_API_KEY="your-token-here"
```

Or create a `.env` file (already in `.gitignore`):
```
AIRNOW_API_KEY=your-key-here
NOAA_API_KEY=your-token-here
```

### 4. Run the Notebooks in Order

```
01_data_collection → 02_eda → 03_model
```

---

## What You'll Learn

- Calling REST APIs with `requests` and handling pagination
- Merging datasets from two different federal sources on date + location
- Feature engineering: lag features, rolling averages, day-of-week
- Regression with **scikit-learn** (Linear Regression → Random Forest → XGBoost)
- Model evaluation: MAE, RMSE, R²
- Visualizing predictions vs. actuals

---

## The ML Problem

**Input features (X):**
- Yesterday's AQI (lag-1)
- AQI from 2 and 3 days ago (lag-2, lag-3)
- 7-day rolling average AQI
- Temperature, wind speed, humidity, precipitation (from NOAA)
- Day of week, month (seasonal patterns)

**Target (y):**
- Tomorrow's AQI value (regression)
- *Optional extension:* AQI category (Good/Moderate/Unhealthy — classification)

---

## Extensions (Once the Baseline Works)

- [ ] Try an LSTM for time-series forecasting
- [ ] Add wildfire season as a binary feature (summer/fall)
- [ ] Swap city — does the model generalize?
- [ ] Build a simple Streamlit dashboard to show predictions
- [ ] Compare PM2.5 vs. Ozone as separate targets

---

## Data Sources

- **EPA AirNow API** — https://docs.airnowapi.org/  
  Real-time and historical AQI observations, 2,500+ monitoring stations
- **NOAA Climate Data Online (CDO) API** — https://www.ncei.noaa.gov/cdo-web/webservices/v2  
  Daily weather summaries (GHCND dataset)
