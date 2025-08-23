import streamlit as st
import os
from io import BytesIO
from dotenv import load_dotenv
import requests # New import for geocoding

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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="ClimateLens – Climate Risk Report", page_icon="🌍", layout="centered")
st.title("ClimateLens – Climate & ESG Report Generator 🌍")

if not ENVIROTRUST_API_KEY:
    st.error("Missing ENVIROTRUST_API_KEY in your .env file. See README.")
    st.stop()

# New geocoding function
def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "ClimateLensApp/1.0 (https://yourwebsite.com/contact)" # User should replace with actual contact info
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Geocoding API error: {e}")
        return None, None
    except ValueError:
        st.error("Could not parse geocoding response.")
        return None, None

with st.form("address_form"):
    address = st.text_input("Enter Address", "Marienplatz, Munich, Germany")
    submitted = st.form_submit_button("Generate Report")

if submitted:
    lat, lon = geocode_address(address)
    if lat is None or lon is None:
        st.error("Could not find coordinates for the given address. Please try a different address.")
        st.stop()
else:
    st.info("Enter an address and click **Generate Report**.")
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
with st.spinner("Rendering charts... (This may take a moment for AI narrative generation.)"):
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
with st.spinner("Generating AI narrative... (This may take a moment for AI narrative generation.)"):
    ai = AIWriter(openai_api_key=OPENAI_API_KEY)
    narrative = ai.generate_sections(
        lat=lat,
        lon=lon,
        address=address,
        risk_score=risk_score,
        flood_zone=flood_zone,
        wildfire_now=wildfire_now,
        **chart_paths
    )

st.success("Narrative ready ✍️")
st.write(narrative)

# -------------------------
# Build PDF
# -------------------------
with st.spinner("Building PDF... (This may take a moment for AI narrative generation.)"):
    pdf_bytes = build_pdf(
        lat=lat,
        lon=lon,
        address=address,
        risk_score=risk_score,
        flood_zone=flood_zone,
        charts=chart_paths,
        narrative=narrative,
    )

st.download_button(
    label="⬇️ Download Climate & ESG Report (PDF)",
    data=pdf_bytes,
    file_name="climate_esg_report.pdf",
    mime="application/pdf",
)