"""
utils/airnow.py
Helper functions for the EPA AirNow API.
Docs: https://docs.airnowapi.org/
"""

import os
import time
import requests
import pandas as pd
from datetime import date, timedelta


BASE_URL = "https://www.airnowapi.org/aq"


def get_api_key() -> str:
    key = os.getenv("AIRNOW_API_KEY")
    if not key:
        raise EnvironmentError(
            "AIRNOW_API_KEY not set. "
            "Register at https://docs.airnowapi.org/ and set the env var."
        )
    return key


def fetch_observation(zip_code: str, obs_date: date) -> list[dict]:
    """
    Fetch daily AQI observation for a ZIP code on a specific date.
    Returns a list of pollutant records (PM2.5, Ozone, etc.)
    """
    params = {
        "format": "application/json",
        "zipCode": zip_code,
        "date": obs_date.strftime("%Y-%m-%dT00-0000"),
        "distance": 25,
        "API_KEY": get_api_key(),
    }
    resp = requests.get(f"{BASE_URL}/observation/zipCode/historical/", params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_date_range(
    zip_code: str,
    start: date,
    end: date,
    pollutant: str = "PM2.5",
    sleep_sec: float = 1.0,
) -> pd.DataFrame:
    """
    Loop over a date range and collect AQI observations into a DataFrame.

    Args:
        zip_code:   5-digit ZIP code string, e.g. "98040"
        start:      First date to fetch
        end:        Last date to fetch (inclusive)
        pollutant:  "PM2.5" or "OZONE" — which parameter to keep
        sleep_sec:  Polite delay between requests (API limit: 500/hr)

    Returns:
        DataFrame with columns: date, aqi, pollutant, category
    """
    records = []
    current = start
    total = (end - start).days + 1

    print(f"Fetching {total} days of AirNow data for ZIP {zip_code}...")

    while current <= end:
        try:
            data = fetch_observation(zip_code, current)
            for entry in data:
                if entry.get("ParameterName", "").upper() == pollutant.upper():
                    records.append({
                        "date": current,
                        "aqi": entry.get("AQI"),
                        "pollutant": entry.get("ParameterName"),
                        "category": entry.get("Category", {}).get("Name"),
                    })
        except requests.HTTPError as e:
            print(f"  Warning: {current} — HTTP {e.response.status_code}, skipping.")
        except Exception as e:
            print(f"  Warning: {current} — {e}, skipping.")

        current += timedelta(days=1)
        time.sleep(sleep_sec)

    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    print(f"Done. {len(df)} records collected.")
    return df


def aqi_to_category(aqi: int) -> str:
    """Map a numeric AQI value to its EPA category string."""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"
