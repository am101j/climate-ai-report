# app.py
import streamlit as st
import requests
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
import os
from dotenv import load_dotenv
import tempfile

# ----------------------------
# Load .env
# ----------------------------
load_dotenv()
API_KEY = os.getenv("ENVIROTRUST_API_KEY")
if not API_KEY:
    st.error("API key not found. Please set ENVIROTRUST_API_KEY in .env file.")

# ----------------------------
# Config
# ----------------------------
API_BASE = "https://api.envirotrust.eu/api/climate_risk"
HEADERS = {"x-api-key": API_KEY}

# ----------------------------
# Functions
# ----------------------------

st.write("API_KEY loaded:", API_KEY is not None)
st.write("API_KEY:", API_KEY)

def get_risk_scores(lat, lon):
    """Call Envirotrust API for climate risk scores"""
    url = f"{API_BASE}/risk_score"
    params = {"latitude": lat, "longitude": lon}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API Error: {response.status_code} - {response.text}")
        return None

def generate_charts(scores):
    """Generate matplotlib charts and return them as BytesIO images"""
    charts = {}
    labels = ["Air Quality", "Flood Risk", "Wildfire Risk"]
    values = [scores["scores"][key] for key in ["air_quality", "flood_risk", "wildfire_risk"]]
    
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=["skyblue", "salmon", "orange"])
    ax.set_ylim(0, 10)
    ax.set_title("Climate Risk Scores")
    charts["bar_chart"] = fig
    
    return charts

def create_pdf(scores, charts):
    """Create a PDF with scores and charts"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Climate Risk Report", ln=True, align="C")
    
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Location: ({scores['location']['latitude']}, {scores['location']['longitude']})", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, f"Air Quality Risk: {scores['scores']['air_quality']}", ln=True)
    pdf.cell(0, 10, f"Flood Risk: {scores['scores']['flood_risk']}", ln=True)
    pdf.cell(0, 10, f"Wildfire Risk: {scores['scores']['wildfire_risk']}", ln=True)
    
    for fig in charts.values():
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            fig.savefig(tmpfile.name, format='PNG')  # save chart to temp file
            pdf.image(tmpfile.name, w=180)
    
    pdf_bytes = pdf.output(dest="S").encode('latin1')  # returns PDF as bytes
    pdf_output = BytesIO(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output
# ----------------------------
# Streamlit App
# ----------------------------
st.title("Climate Risk Report Generator 🌍")

lat = st.number_input("Latitude (-90 to 90)", min_value=-90.0, max_value=90.0, value=51.5)
lon = st.number_input("Longitude (-180 to 180)", min_value=-180.0, max_value=180.0, value=-0.1)

if st.button("Generate Report") and API_KEY:
    scores = get_risk_scores(lat, lon)
    if scores:
        st.success("Data retrieved successfully!")
        charts = generate_charts(scores)
        
        st.subheader("Charts")
        for fig in charts.values():
            st.pyplot(fig)
        
        pdf_file = create_pdf(scores, charts)
        st.download_button(
            label="Download PDF Report",
            data=pdf_file,
            file_name="climate_risk_report.pdf",
            mime="application/pdf"
        )
