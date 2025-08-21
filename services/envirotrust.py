import os
import requests

BASE = "https://api.envirotrust.eu"

def _get(path, params=None, stream=False):
    import os
    import requests
    headers = {"x-api-key": os.getenv("ENVIROTRUST_API_KEY")}
    url = f"{BASE}{path}"
    r = requests.get(url, headers=headers, params=params, stream=stream, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"EnviroTrust API error {r.status_code}: {r.text}")

    if stream:
        return r

    # Ensure JSON response
    try:
        return r.json()
    except ValueError:
        raise RuntimeError(f"EnviroTrust API returned non-JSON response: {r.text}")



# 1) Composite risk (AQ, flood, wildfire)
def get_risk_score(lat: float, lon: float):
    return _get("/api/climate_risk/risk_score", {"latitude": lat, "longitude": lon})

# 2) Air quality time-series (daily & monthly)
def get_air_quality_daily(lat: float, lon: float):
    return _get("/api/airquality/timeseries-daily", {"latitude": lat, "longitude": lon})

def get_air_quality_monthly(lat: float, lon: float):
    return _get("/api/airquality/timeseries-monthly", {"latitude": lat, "longitude": lon})

# 3) Flood zone boolean
def get_flood_zone_current(lat: float, lon: float):
    return _get("/api/flood/zone-current", {"latitude": lat, "longitude": lon})

# 4) Wildfire current and timeseries
def get_wildfire_current(lat: float, lon: float):
    return _get("/api/wildfire/risk-current", {"latitude": lat, "longitude": lon})

def get_wildfire_timeseries(lat: float, lon: float):
    return _get("/api/wildfire/timeseries", {"latitude": lat, "longitude": lon})

# 5) Heat/Wind: daily & climate scenarios time series
def get_heat_wind_daily(lat: float, lon: float):
    return _get("/api/heat-wind/daily", {"latitude": lat, "longitude": lon})

def get_heat_wind_timeseries(lat: float, lon: float):
    return _get("/api/heat-wind/timeseries", {"latitude": lat, "longitude": lon})
