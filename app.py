import streamlit as st
import os
from io import BytesIO
from dotenv import load_dotenv

from services.envirotrust import (
    get_risk_score,
    get_air_quality_daily,
    get_air_quality_monthly,
    get_flood_zone_current,
    get_wildfire_current,
    get_wildfire_timeseries,
    get_heat_wind_daily,
    get_heat_wind_timeseries,
)
from services.ai_writer import AIWriter
from viz.charts import (
    plot_risk_score_bar,
    plot_air_quality_gauges,
    plot_wildfire_timeseries,
    plot_heat_wind_scenarios,
    plot_recent_daily_weather,
)
from report.pdf_builder import build_pdf

load_dotenv()
ENVIROTRUST_API_KEY = os.getenv("ENVIROTRUST_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")  # optional but recommended
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="ClimateLens – Climate Risk Report", page_icon="🌍", layout="centered")
st.title("ClimateLens – Climate & ESG Report Generator 🌍")

if not ENVIROTRUST_API_KEY:
    st.error("Missing ENVIROTRUST_API_KEY in your .env file. See README.")
    st.stop()

with st.form("coords"):
    col1, col2 = st.columns(2)
    lat = col1.number_input("Latitude (-90 to 90)", min_value=-90.0, max_value=90.0, value=48.097)
    lon = col2.number_input("Longitude (-180 to 180)", min_value=-180.0, max_value=180.0, value=11.506)
    submitted = st.form_submit_button("Generate Report")

if not submitted:
    st.info("Enter latitude/longitude and click **Generate Report**.")
    st.stop()

# -------------------------
# Fetch data
# -------------------------
with st.spinner("Fetching climate data..."):
    try:
        risk_score = get_risk_score(lat, lon)
        aq_daily = get_air_quality_daily(lat, lon)
        aq_monthly = get_air_quality_monthly(lat, lon)
        flood_zone = get_flood_zone_current(lat, lon)
        wildfire_now = get_wildfire_current(lat, lon)
        wildfire_ts = get_wildfire_timeseries(lat, lon)
        heatwind_daily = get_heat_wind_daily(lat, lon)
        heatwind_ts = get_heat_wind_timeseries(lat, lon)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

st.success("Data retrieved ✅")

# -------------------------
# Make charts (saved to temp files)
# -------------------------
with st.spinner("Rendering charts..."):
    chart_paths = {}
    chart_paths["risk_bar"] = plot_risk_score_bar(risk_score)
    chart_paths["aq_gauges"] = plot_air_quality_gauges(aq_daily)
    chart_paths["wildfire_ts"] = plot_wildfire_timeseries(wildfire_ts)
    chart_paths["heatwind_scen"] = plot_heat_wind_scenarios(heatwind_ts)
    chart_paths["recent_daily"] = plot_recent_daily_weather(heatwind_daily)

st.subheader("Preview")
for p in chart_paths.values():
    st.image(p, use_column_width=True)

# -------------------------
# AI Narrative
# -------------------------
with st.spinner("Generating AI narrative..."):
    ai = AIWriter(groq_api_key=GROQ_API_KEY)
    narrative = ai.generate_sections(
        lat=lat,
        lon=lon,
        risk_score=risk_score,
        aq_daily=aq_daily,
        aq_monthly=aq_monthly,
        flood_zone=flood_zone,
        wildfire_now=wildfire_now,
        wildfire_ts=wildfire_ts,
        heatwind_daily=heatwind_daily,
        heatwind_ts=heatwind_ts,
    )

st.success("Narrative ready ✍️")

# -------------------------
# Build PDF
# -------------------------
with st.spinner("Building PDF..."):
    pdf_bytes = build_pdf(
        lat=lat,
        lon=lon,
        risk_score=risk_score,
        flood_zone=flood_zone,
        wildfire_now=wildfire_now,
        charts=chart_paths,
        narrative=narrative,
    )

st.download_button(
    label="⬇️ Download Climate & ESG Report (PDF)",
    data=pdf_bytes,
    file_name="climate_esg_report.pdf",
    mime="application/pdf",
)
