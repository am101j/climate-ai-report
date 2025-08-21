from fpdf import FPDF
from io import BytesIO

def sanitize_text(text: str) -> str:
    """Replace characters not supported by Latin-1."""
    if not text:
        return ""
    replacements = {
        "–": "-",   # en-dash
        "—": "-",   # em-dash
        "’": "'",   # curly apostrophe
        "“": '"',
        "”": '"',
        "•": "-",   # bullet
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def build_pdf(lat, lon, risk_score, flood_zone, wildfire_now, charts: dict, narrative: dict) -> BytesIO:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Use built-in font only
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, sanitize_text("ClimateLens – Climate & ESG Report"), ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.ln(4)
    pdf.cell(0, 8, f"Location: ({lat:.5f}, {lon:.5f})", ln=True)

    # Key scores
    scores = risk_score.get("scores", {})
    pdf.cell(0, 8, f"Air Quality Risk (0-10): {scores.get('air_quality','N/A')}", ln=True)
    pdf.cell(0, 8, f"Flood Risk (0 or 10): {scores.get('flood_risk','N/A')} (Flood Zone: {flood_zone.get('flood_zone')})", ln=True)
    pdf.cell(0, 8, f"Wildfire Risk (0-10): {scores.get('wildfire_risk','N/A')}", ln=True)

    # Charts
    for label in ["risk_bar", "aq_gauges", "wildfire_ts", "heatwind_scen", "recent_daily"]:
        if charts.get(label):
            pdf.ln(5)
            pdf.image(charts[label], w=180)

    # AI Sections
    def write_section(title, body):
        if not body:
            return
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, sanitize_text(title), ln=True)
        pdf.set_font("Arial", "", 12)
        for line in sanitize_text(body).split("\n"):
            pdf.multi_cell(0, 7, line)

    write_section("1. Executive Summary", narrative.get("executive_summary") or narrative.get("raw"))
    write_section("2. Local Climate Risk", narrative.get("local_climate_risk"))
    write_section("3. Implications for Property Value & Insurability", narrative.get("implications"))
    write_section("4. ESG & Resilience Opportunities", narrative.get("esg_opportunities"))
    write_section("5. Final Verdict", narrative.get("verdict"))

    pdf_bytes = pdf.output(dest="S").encode("latin1", errors="replace")
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    return buf
