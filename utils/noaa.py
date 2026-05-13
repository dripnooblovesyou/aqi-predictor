"""
utils/noaa.py
Helper functions for the NOAA Climate Data Online (CDO) API.
Docs: https://www.ncei.noaa.gov/cdo-web/webservices/v2
Token: https://www.ncei.noaa.gov/cdo-web/token (emailed to you, free)
"""

import os
import time
import requests
import pandas as pd
from datetime import date


BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"

# NOAA GHCND daily weather elements we care about
# TMAX/TMIN in tenths of °C, PRCP in tenths of mm, AWND in tenths of m/s
ELEMENTS = ["TMAX", "TMIN", "PRCP", "AWND"]


def get_api_key() -> str:
    key = os.getenv("NOAA_API_KEY")
    if not key:
        raise EnvironmentError(
            "NOAA_API_KEY not set. "
            "Request a free token at https://www.ncei.noaa.gov/cdo-web/token"
        )
    return key


def find_station(zip_code: str, start: date, end: date) -> str | None:
    """
    Find the best NOAA weather station near a ZIP code that has data
    for the given date range. Returns the station ID string or None.

    Tip: You can also look up station IDs manually at:
    https://www.ncei.noaa.gov/cdo-web/search
    """
    params = {
        "datasetid": "GHCND",
        "locationid": f"ZIP:{zip_code}",
        "datatypeid": ",".join(ELEMENTS),
        "startdate": start.isoformat(),
        "enddate": end.isoformat(),
        "limit": 10,
        "sortfield": "datacoverage",
        "sortorder": "desc",
    }
    resp = requests.get(
        f"{BASE_URL}/stations",
        params=params,
        headers={"token": get_api_key()},
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None
    station = results[0]
    print(f"Using station: {station['id']} — {station['name']} "
          f"(coverage: {station['datacoverage']:.0%})")
    return station["id"]


def fetch_weather(
    station_id: str,
    start: date,
    end: date,
    sleep_sec: float = 0.4,
) -> pd.DataFrame:
    """
    Fetch daily weather summaries from NOAA GHCND for a station.
    NOAA CDO API returns max 1000 records per request, so we paginate
    in 1-year chunks to stay within limits.

    Returns:
        DataFrame with columns: date, tmax_c, tmin_c, tavg_c, prcp_mm, wind_ms
    """
    all_data = []
    # NOAA CDO allows max 1-year window per request, so chunk if needed
    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(
            date(chunk_start.year, 12, 31),
            end
        )
        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "datatypeid": ",".join(ELEMENTS),
            "startdate": chunk_start.isoformat(),
            "enddate": chunk_end.isoformat(),
            "limit": 1000,
            "units": "metric",
        }
        resp = requests.get(
            f"{BASE_URL}/data",
            params=params,
            headers={"token": get_api_key()},
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        all_data.extend(results)
        print(f"  Fetched weather {chunk_start} → {chunk_end}: {len(results)} records")
        chunk_start = date(chunk_start.year + 1, 1, 1)
        time.sleep(sleep_sec)

    if not all_data:
        return pd.DataFrame()

    # Pivot from long to wide format
    df_long = pd.DataFrame(all_data)
    df_long["date"] = pd.to_datetime(df_long["date"]).dt.date

    df_wide = df_long.pivot_table(
        index="date", columns="datatype", values="value", aggfunc="mean"
    ).reset_index()

    # Rename and scale columns
    rename = {
        "TMAX": "tmax_c",
        "TMIN": "tmin_c",
        "PRCP": "prcp_mm",
        "AWND": "wind_ms",
    }
    df_wide = df_wide.rename(columns={k: v for k, v in rename.items() if k in df_wide.columns})

    # Add average temp if both max and min present
    if "tmax_c" in df_wide.columns and "tmin_c" in df_wide.columns:
        df_wide["tavg_c"] = (df_wide["tmax_c"] + df_wide["tmin_c"]) / 2

    df_wide["date"] = pd.to_datetime(df_wide["date"])
    return df_wide.sort_values("date").reset_index(drop=True)
