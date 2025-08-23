import os
import tempfile
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.ticker as ticker
import matplotlib.dates as mdates

# Global style settings
sns.set_theme(style="whitegrid")
PALETTE = sns.color_palette("viridis", 8)

def _save_current_fig(title):
    """Save current matplotlib figure to a temporary file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    path = tmp.name
    tmp.close()
    try:
        plt.suptitle(title, fontsize=18, weight="bold", y=1.02)
        plt.savefig(path, dpi=150, bbox_inches="tight")
    finally:
        plt.close()
    return path

# -------------------------
# Risk Score Bar
# -------------------------
def plot_risk_score_bar(risk_score) -> str:
    scores = risk_score.get("scores", {}) if isinstance(risk_score, dict) else {}
    labels = ["Air Quality", "Flood", "Wildfire"]
    vals = [
        scores.get("air_quality", 0) or 0,
        scores.get("flood_risk", 0) or 0,
        scores.get("wildfire_risk", 0) or 0,
    ]

    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x=labels, y=vals, palette=PALETTE, width=0.6)
    ax.set_ylim(0, 10)
    ax.set_ylabel("Risk Level (0-10)", fontsize=12)
    for p in ax.patches:
        ax.annotate(
            f"{p.get_height():.1f}",
            (p.get_x() + p.get_width() / 2., p.get_height()),
            ha='center',
            va='center',
            xytext=(0, 5),
            textcoords='offset points',
            weight="bold"
        )
    return _save_current_fig("Composite Climate Risk Scores")

# -------------------------
# Air Quality Snapshot
# -------------------------
def plot_air_quality_gauges(aq_data) -> str:
    latest_aqi, latest_pm25 = 0, 0
    items = []

    if isinstance(aq_data, dict):
        items = aq_data.get("air_quality_timeseries", [])
    elif isinstance(aq_data, list):
        items = aq_data

    if items and isinstance(items[-1], dict):
        last = items[-1]
        latest_aqi = last.get("air_quality_index", 0)
        latest_pm25 = last.get("pm2_5", 0)

    plt.figure(figsize=(6, 5))
    ax = sns.barplot(x=["AQI", "PM2.5"], y=[latest_aqi, latest_pm25], palette=PALETTE, width=0.5)
    ax.set_ylabel("Value", fontsize=12)
    for p in ax.patches:
        ax.annotate(
            f"{p.get_height():.1f}",
            (p.get_x() + p.get_width() / 2., p.get_height()),
            ha='center',
            va='center',
            xytext=(0, 5),
            textcoords='offset points',
            weight="bold"
        )
    return _save_current_fig("Latest Air Quality Snapshot")

# -------------------------
# Wildfire Timeseries
# -------------------------
def plot_wildfire_timeseries(api_data) -> str:
    wf_ts = api_data.get("wildfire_risk_timeseries_data", {})
    df = pd.DataFrame(wf_ts).T
    # Remove latitude and longitude columns if they exist
    if "latitude" in df.columns:
        df = df.drop(columns=["latitude"])
    if "longitude" in df.columns:
        df = df.drop(columns=["longitude"])
    if "year" in df.columns:
        df = df.drop(columns=["year"])
    df = df.reset_index().rename(columns={"index": "year"})

    if df.empty:
        return _save_current_fig("Wildfire Danger Days per Year")

    df = df.melt(id_vars="year", var_name="danger_level", value_name="days")

    plt.figure(figsize=(10, 6))
    ax = sns.lineplot(
        data=df,
        x="year",
        y="days",
        hue="danger_level",
        palette=PALETTE,
        marker="o",
        lw=2.5
    )
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Days", fontsize=12)
    ax.legend(title="Danger Level")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, prune='both'))
    plt.xticks(rotation=45, ha="right")
    return _save_current_fig("Wildfire Danger Days per Year")

# -------------------------
# Heat & Wind Climate Scenarios
# -------------------------
def plot_heat_wind_scenarios(api_data) -> str:
    hw_ts = api_data.get("heat_wind_timeseries_data", [])
    df = pd.DataFrame(hw_ts)
    if df.empty:
        return _save_current_fig("Heat & Wind Climate Scenarios")

    # Remove 'daily max temperature' scenarios as per API documentation
    if 'daily max temperature rcp45(K)' in df.columns:
        df = df.drop(columns=['daily max temperature rcp45(K)'])
    if 'daily max temperature rcp85(K)' in df.columns:
        df = df.drop(columns=['daily max temperature rcp85(K)'])

    df = df.melt(id_vars="year", var_name="scenario", value_name="days")

    # Filter to plot only one of each heatwaves, consecutive dry days, and extreme wind speed
    desired_scenarios = [
        'heatwaves_rcp45',
        'consecutive_dry_days_rcp45',
        'extreme_wind_speed_days_rcp45'
    ]
    df = df[df['scenario'].isin(desired_scenarios)]

    plt.figure(figsize=(10, 6))
    ax = sns.lineplot(
        data=df,
        x="year",
        y="days",
        hue="scenario",
        style="scenario",
        palette=PALETTE,
        markers=True,
        dashes=False,
        lw=2.5
    )
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Days", fontsize=12)
    ax.legend(title="Scenario")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, prune='both'))
    plt.xticks(rotation=45, ha="right")
    return _save_current_fig("Heat & Wind Climate Scenarios")

# -------------------------
# Recent Daily Weather
# -------------------------
def plot_recent_daily_weather(hw_daily) -> str:
    if isinstance(hw_daily, dict) and "heat_wind_daily_data" in hw_daily:
        hw_daily = hw_daily["heat_wind_daily_data"]
    elif not isinstance(hw_daily, list):
        hw_daily = []

    df = pd.DataFrame(hw_daily[-30:])
    if df.empty:
        return _save_current_fig("Recent Daily Weather (Last 30 Days)")

    # Remove 'year' column as per API documentation
    if 'year' in df.columns:
        df = df.drop(columns=['year'])

    # Remove '2m temperature(K)' column as per user request
    if '2m temperature(K)' in df.columns:
        df = df.drop(columns=['2m temperature(K)'])

    df["date"] = pd.to_datetime(df["date"])
    df = df.melt(id_vars="date", var_name="measurement", value_name="value")

    plt.figure(figsize=(12, 6))
    ax = sns.lineplot(
        data=df,
        x="date",
        y="value",
        hue="measurement",
        palette=PALETTE,
        marker="o",
        lw=2
    )

    # Format x-axis to show month & day only
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=45, ha="right")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    ax.legend(title="Measurement")
    return _save_current_fig("Recent Daily Weather (Last 30 Days)")
