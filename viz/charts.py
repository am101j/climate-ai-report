import os
import tempfile
import matplotlib.pyplot as plt
import json

def _save_current_fig():
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plt.savefig(tmp.name, dpi=160, bbox_inches="tight")
    plt.close()
    return tmp.name

def plot_risk_score_bar(risk_score) -> str:
    # Safely get scores dict
    if isinstance(risk_score, dict):
        scores = risk_score.get("scores", {}) if "scores" in risk_score else {}
    else:
        scores = {}
    labels = ["Air Quality", "Flood", "Wildfire"]
    vals = [
        scores.get("air_quality", 0) or 0,
        scores.get("flood_risk", 0) or 0,
        scores.get("wildfire_risk", 0) or 0,
    ]
    plt.figure()
    plt.bar(labels, vals)
    plt.ylim(0, 10)
    plt.title("Composite Climate Risk Scores (0–10)")
    return _save_current_fig()

def plot_air_quality_gauges(aq_data) -> str:
    latest_aqi, latest_pm25 = 0, 0
    items = []

    if isinstance(aq_data, dict):
        # ✅ match your API key
        items = aq_data.get("air_quality_timeseries", [])
    elif isinstance(aq_data, list):
        items = aq_data

    if items:
        last = items[-1]  # most recent record
        if isinstance(last, dict):
            latest_aqi = last.get("air_quality_index", 0)
            latest_pm25 = last.get("pm2_5", 0)

    plt.figure()
    plt.bar(["AQI", "PM2.5"], [latest_aqi, latest_pm25])
    plt.title("Latest Air Quality Snapshot")
    return _save_current_fig()


def plot_wildfire_timeseries(api_data) -> str:
    """Plot wildfire danger days timeseries from API data and return saved image path."""
    wf_ts = api_data.get("wildfire_risk_timeseries_data", {})
    
    years, high, very_high, moderate = [], [], [], []

    if isinstance(wf_ts, dict):
        for y_str, rec in wf_ts.items():
            if not isinstance(rec, dict):
                continue
            try:
                y = int(y_str)
            except ValueError:
                continue
            years.append(y)
            high.append(rec.get("days_high_fire_danger", 0))
            very_high.append(rec.get("days_very_high_fire_danger", 0))
            moderate.append(rec.get("days_moderate_fire_danger", 0))

    if not years:
        years, high, very_high, moderate = [0], [0], [0], [0]

    # Sort by year
    order = sorted(range(len(years)), key=lambda i: years[i])
    years = [years[i] for i in order]
    high = [high[i] for i in order]
    very_high = [very_high[i] for i in order]
    moderate = [moderate[i] for i in order]

    # Plot
    plt.figure()
    plt.plot(years, moderate, label="Moderate")
    plt.plot(years, high, label="High")
    plt.plot(years, very_high, label="Very High")
    plt.title("Wildfire Danger Days per Year")
    plt.xlabel("Year")
    plt.ylabel("Days")
    plt.legend()
    return _save_current_fig()

def plot_heat_wind_scenarios(api_data) -> str:
    """Plot heatwaves and extreme wind days timeseries from API data."""
    hw_ts = api_data.get("heat_wind_timeseries_data", [])
    if not isinstance(hw_ts, list):
        hw_ts = []

    years, hw45, hw85, ew45, ew85 = [], [], [], [], []

    for row in hw_ts:
        if not isinstance(row, dict):
            continue
        years.append(int(row.get("year", 0)))
        hw45.append(row.get("heatwaves_rcp45", 0))
        hw85.append(row.get("heatwaves_rcp85", 0))
        ew45.append(row.get("extreme_wind_speed_days_rcp45", 0))
        ew85.append(row.get("extreme_wind_speed_days_rcp85", 0))

    if not years:
        years, hw45, hw85, ew45, ew85 = [0], [0], [0], [0], [0]

    # Sort by year
    order = sorted(range(len(years)), key=lambda i: years[i])
    years = [years[i] for i in order]
    hw45 = [hw45[i] for i in order]
    hw85 = [hw85[i] for i in order]
    ew45 = [ew45[i] for i in order]
    ew85 = [ew85[i] for i in order]

    # Plot
    plt.figure()
    plt.plot(years, hw45, label="Heatwaves RCP4.5")
    plt.plot(years, hw85, label="Heatwaves RCP8.5")
    plt.plot(years, ew45, label="Extreme Wind Days RCP4.5")
    plt.plot(years, ew85, label="Extreme Wind Days RCP8.5")
    plt.title("Heat & Wind Climate Scenarios")
    plt.xlabel("Year")
    plt.ylabel("Count")
    plt.legend()
    return _save_current_fig()

def plot_recent_daily_weather(hw_daily) -> str:
    # unwrap if dict with list inside
    if isinstance(hw_daily, dict) and "heat_wind_daily_data" in hw_daily:
        hw_daily = hw_daily["heat_wind_daily_data"]
    elif not isinstance(hw_daily, list):
        hw_daily = []

    dates, temps, gusts = [], [], []

    for row in hw_daily[-30:]:
        if not isinstance(row, dict):
            continue
        dates.append(row.get("date"))
        temps.append(row.get("2m_temperature(C)", row.get("temp_c", 0)))
        gusts.append(row.get("10m wind gust(m/s)", row.get("wind_gust_ms", 0)))

    plt.figure()
    plt.plot(dates, temps, label="2m Temperature (°C)")
    plt.plot(dates, gusts, label="10m Wind Gust (m/s)")
    plt.title("Recent Daily Weather")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    return _save_current_fig()
