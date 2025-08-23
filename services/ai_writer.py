import logging
import json
import os
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

DEFAULT_MODEL = "gpt-5"

SYSTEM_PROMPT = """
You are a world-class climate-risk and ESG consultant producing reports for high-value residential properties.
You should use plain language and NOT any links or reference URLs.
STRICT SCHEMA (MUST FOLLOW EXACTLY):
{
  "executive_summary": {
    "title": "Executive Summary",
    "subsections": [
      {
        "subtitle": "Subsection Title",
        "paragraphs": ["Paragraph text..."],  # 2–3 short paragraphs
        "bullets": ["Bullet point..."],       # optional, 3–5 bullets
        "charts": []
      }
    ]
  },
  "market_analysis": {
    "title": "Market Analysis",
    "subsections": [
      {
        "subtitle": "Subsection Title",
        "paragraphs": ["Paragraph text..."],  # 2–3 short paragraphs
        "bullets": ["Bullet point..."],       # optional, 3–5 bullets
        "charts": ["wildfire_ts", "heatwind_scen"]
      }
    ]
  },
  "climate_and_esg_risks": {
    "title": "Climate and ESG Risks",
    "subsections": [
      {
        "subtitle": "Subsection Title",
        "paragraphs": ["Paragraph text..."],  # 2–3 short paragraphs
        "bullets": ["Bullet point..."],       # optional, 3–5 bullets
        "charts": ["risk_bar", "aq_gauges", "recent_daily"]
      }
    ]
  },
  "final_verdict": {
    "title": "Final Verdict",
    "subsections": [
      {
        "subtitle": "Subsection Title",
        "paragraphs": ["Paragraph text..."],
        "bullets": ["Bullet point..."],
        "charts": []
      }
    ]
  }
}

For 'market_analysis', include:
- Average property prices in the area
- Typical rental/valuation trends
- Liquidity, insurance, and resilience premiums
Do NOT output URLs or any links. Use plain language.

RULES:
1. **MUST FOLLOW SCHEMA EXACTLY**.
2. NO extra keys, fields, or URLs.
3. Paragraphs: 2–3 short paragraphs per subsection.
4. Bullets: optional, 3–5 bullets if present.
5. Charts: choose from ["risk_bar","aq_gauges","wildfire_ts","heatwind_scen","recent_daily"] and no repeats.
6. Output ONLY JSON. DO NOT add any explanation or text outside the JSON.
"""

AVAILABLE_CHARTS = ["risk_bar", "aq_gauges", "wildfire_ts", "heatwind_scen", "recent_daily"]

def _build_prompt(lat, lon, address, risk_score, flood_zone, wildfire_now, **kwargs):
    chart_info = []
    for chart in AVAILABLE_CHARTS:
        if kwargs.get(chart):
            chart_info.append(f"- '{chart}': include if relevant")

    chart_text = "Charts guidance:\n" + "\n".join(chart_info) if chart_info else ""

    return f"""
{SYSTEM_PROMPT}

Generate a report for the property at:
Address: {address}
Latitude: {lat}
Longitude: {lon}

Key Data:
- Air Quality Risk: {risk_score.get("scores", {}).get("air_quality")}
- Flood Risk: {risk_score.get("scores", {}).get("flood_risk")}
- Wildfire Risk: {risk_score.get("scores", {}).get("wildfire_risk")}
- Flood Zone: {flood_zone.get("flood_zone")}
- Wildfire Risk (1km radius): {wildfire_now.get("properties", {}).get("fire_risk_class")}

{chart_text}

**CRITICAL:** Output must be a single valid JSON object strictly following the schema above, with no extra text, no URLs, and no deviations.
"""

class AIWriter:
    def __init__(self, openai_api_key: str = None):
        self.client = OpenAI(api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"))

    def _call_openai(self, prompt: str) -> str:
        logging.info("Calling GPT-5 API...")
        try:
            response = self.client.responses.create(
                model=DEFAULT_MODEL,
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            output_text = response.output_text
            logging.info("GPT-5 response received.")
            return output_text
        except Exception as e:
            logging.error(f"OpenAI API call failed: {e}")
            raise

    def generate_sections(self, lat, lon, address, risk_score, flood_zone, wildfire_now, **kwargs) -> dict:
      prompt = _build_prompt(lat, lon, address, risk_score, flood_zone, wildfire_now, **kwargs)
      raw_output = self._call_openai(prompt)

      try:
          parsed_json = json.loads(raw_output)
          logging.info("GPT-5 JSON parsed successfully.")
      except json.JSONDecodeError as e:
          logging.error(f"Failed to parse JSON: {e}\nRaw output:\n{raw_output}")
          raise ValueError("GPT-5 returned invalid JSON") from e

      # Validate top-level sections and subsections
      required_sections = ["executive_summary", "market_analysis", "climate_and_esg_risks", "final_verdict"]
      for sec in required_sections:
          if sec not in parsed_json:
              raise ValueError(f"Missing required top-level section: {sec}")
          if "title" not in parsed_json[sec] or "subsections" not in parsed_json[sec]:
              raise ValueError(f"Section '{sec}' missing 'title' or 'subsections'")

      # Deduplicate charts globally across all subsections
      used_charts = set()
      for sec in required_sections:
          for sub in parsed_json[sec]["subsections"]:
              if "subtitle" not in sub or "paragraphs" not in sub:
                  raise ValueError(f"A subsection in '{sec}' is missing 'subtitle' or 'paragraphs'")
              
              if "charts" in sub:
                  # Keep only allowed charts
                  sub["charts"] = [c for c in sub["charts"] if c in AVAILABLE_CHARTS]
                  # Keep charts not already used in other subsections
                  new_charts = []
                  for c in sub["charts"]:
                      if c not in used_charts:
                          new_charts.append(c)
                          used_charts.add(c)
                  sub["charts"] = new_charts

      logging.info("GPT-5 JSON validated successfully with unique charts across subsections.")
      return parsed_json

