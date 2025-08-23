from fpdf import FPDF
from io import BytesIO
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Colors
COLOR_BLUE = (0, 102, 204)
COLOR_DARK_GREEN = (0, 100, 0)
COLOR_GREY = (128, 128, 128)


class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*COLOR_GREY)
        self.cell(0, 10, "ClimateLens – Climate & ESG Report", 0, 0, "C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(*COLOR_GREY)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


def safe_multi_cell(pdf, text, w=0, h=8, align='J'):
    """
    Safely wrap text to avoid 'Not enough horizontal space' errors.
    """
    # Replace problematic unicode characters if needed
    if text is None:
        text = ""
    # Replace non-breaking hyphen/dash variants with normal dash
    text = text.replace("–", "-").replace("—", "-")
    # Split very long words manually
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if pdf.get_string_width(test_line) > pdf.w - pdf.l_margin - pdf.r_margin:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    # Write each line
    for line in lines:
        pdf.multi_cell(w, h, line, align=align)
        pdf.ln(0)


def build_pdf(lat, lon, address, risk_score, flood_zone, charts: dict, narrative: dict) -> BytesIO:
    logging.info("Starting PDF build process...")
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=25)

    # --- Register fonts (assumes DejaVu fonts in the same folder) ---
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "DejaVuSans-Oblique.ttf", uni=True)
    pdf.add_font("DejaVu", "BI", "DejaVuSans-BoldOblique.ttf", uni=True)

    pdf.add_page()

    # --- Title Page ---
    pdf.set_font("DejaVu", "B", 36)
    pdf.set_text_color(*COLOR_BLUE)
    safe_multi_cell(pdf, "Climate & ESG Risk Report", h=12, align="C")
    pdf.ln(10)

    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), "ClimateLens Logo.png")
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=85, w=40)
    else:
        logging.warning("Logo not found, using placeholder box.")
        pdf.set_fill_color(230, 230, 230)
        pdf.rect(x=85, y=pdf.get_y(), w=40, h=40, style="F")
    pdf.ln(50)

    # Property address
    pdf.set_font("DejaVu", "", 14)
    pdf.set_text_color(0, 0, 0)
    safe_multi_cell(pdf, f"Property at: {address}", h=10, align="C")
    pdf.ln(20)

    # --- Narrative Sections ---
    section_order = ["executive_summary", "market_analysis", "climate_and_esg_risks", "final_verdict"]
    chart_labels = {
        "risk_bar": "Composite Climate Risk Scores",
        "aq_gauges": "Air Quality Snapshot",
        "wildfire_ts": "Wildfire Danger Trends",
        "heatwind_scen": "Heat & Wind Climate Scenarios",
        "recent_daily": "Recent Daily Weather",
    }

    for section_key in section_order:
        section = narrative.get(section_key)
        if not section:
            continue

        pdf.add_page()
        # Section title
        pdf.set_font("DejaVu", "B", 24)
        pdf.set_text_color(*COLOR_BLUE)
        safe_multi_cell(pdf, section.get("title", ""), h=10)
        pdf.set_draw_color(*COLOR_BLUE)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(10)

        for subsection in section.get("subsections", []):
            # Subtitle
            pdf.set_font("DejaVu", "B", 16)
            pdf.set_text_color(*COLOR_DARK_GREEN)
            safe_multi_cell(pdf, subsection.get("subtitle", ""), h=8)
            pdf.ln(2)

            # Paragraphs
            pdf.set_font("DejaVu", "", 11)
            pdf.set_text_color(0, 0, 0)
            for p in subsection.get("paragraphs", []):
                safe_multi_cell(pdf, p, h=6)
                pdf.ln(1)

            # Bullets
            if subsection.get("bullets"):
                for bullet in subsection.get("bullets", []):
                    safe_multi_cell(pdf, f"  • {bullet}", h=6)
                pdf.ln(2)

            # Charts (avoid repeats)
            if subsection.get("charts"):
                used_charts = set()
                for chart_ref in subsection.get("charts", []):
                    if chart_ref in charts and chart_ref not in used_charts:
                        used_charts.add(chart_ref)
                        pdf.add_page()
                        pdf.set_font("DejaVu", "B", 12)
                        pdf.set_text_color(0, 0, 0)
                        safe_multi_cell(pdf, chart_labels.get(chart_ref, "Chart"), h=8, align="C")
                        page_width = pdf.w - pdf.l_margin - pdf.r_margin
                        chart_width = min(180, page_width)
                        x = (pdf.w - chart_width) / 2
                        pdf.image(charts[chart_ref], x=x, w=chart_width)
                        pdf.ln(5)

    # --- Export PDF ---
    logging.info("Encoding PDF to bytes...")
    try:
        pdf_bytes = pdf.output(dest="S")
        buf = BytesIO(pdf_bytes)
        buf.seek(0)
        logging.info("PDF built successfully.")
        return buf
    except Exception as e:
        logging.error(f"Failed to build PDF: {e}")
        raise
