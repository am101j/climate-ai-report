import logging
import re
import os
from groq import Groq

logging.basicConfig(level=logging.INFO)

DEFAULT_MODEL = "llama-3.3-70b-versatile" 

SYSTEM_PROMPT = """
You are a climate-risk and ESG analyst for residential properties.
Write professional, and decision-useful text for homebuyers.
However the report has to be positive, actually "selling" the property and not undermining the sale process.
if there is something to be careful about the report should mention it, because we need to be frank and trustworthy - but minor things should not be inflated to scare a prospective buyer
Use clear structure, medium sized paragraphs, bullets where relevant.
Avoid jargon, use plain English.
Highlight what matters for property value, insurance, and resilience.
Offer actionable suggestions.
"""

def _build_prompt(lat, lon, risk_score, aq_daily, aq_monthly, flood_zone, wildfire_now, wildfire_ts, heatwind_daily, heatwind_ts):
    return f"""
{SYSTEM_PROMPT}

Location: lat {lat}, lon {lon}

Composite Risk Scores:
- Air quality risk (0-10): {risk_score.get('scores', {}).get('air_quality')}
- Flood risk (0/10): {risk_score.get('scores', {}).get('flood_risk')}
- Wildfire risk (0-10): {risk_score.get('scores', {}).get('wildfire_risk')}

Flood Zone (current): {flood_zone.get('flood_zone')}

Wildfire risk (current window, 1km radius):
{wildfire_now}

Wildfire timeseries (key fields per year):
{list(wildfire_ts.keys())[:10]}

Air quality daily (sample of last 5 rows):
{str(aq_daily)[:800]}

Air quality monthly (first 5 rows):
{str(aq_monthly)[:800]}

Heat/Wind daily (sample of last 5 rows):
{str(heatwind_daily)[:800]}

Heat/Wind scenarios (RCP45/85) – sample:
{str(heatwind_ts)[:1200]}

We want the report to be such that it postively impacts the buyer's decision, convincing them and selling it to them.
Write these sections:
1) Executive Summary – top 3 takeaways for a homebuyer (4–6 sentences)
2) Local Climate Risk – contextualize scores in human terms
3) Implications for Property Value & Insurability – 2–4 bullets
4) ESG & Resilience Opportunities – practical retrofits, shading, green roofs, defensible space
5) Final Verdict – 1 concise paragraph, actionable conclusion
"""

class AIWriter:
    def __init__(self, groq_api_key: str = None):
        self.client = Groq(api_key=groq_api_key or os.environ.get("GROQ_API_KEY"))

    def _call_groq(self, prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 650):
        logging.info("Calling Groq API...")
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.6,
            )
            logging.info("Groq response received")
            return completion.choices[0].message.content

        except Exception as e:
            logging.error(f"Groq API call failed: {e}")
            raise

    def generate_sections(
        self, lat, lon, risk_score, aq_daily, aq_monthly, flood_zone, wildfire_now, wildfire_ts, heatwind_daily, heatwind_ts
    ) -> dict:
        prompt = _build_prompt(
            lat, lon, risk_score, aq_daily, aq_monthly, flood_zone,
            wildfire_now, wildfire_ts, heatwind_daily, heatwind_ts
        )

        full = self._call_groq(prompt)

        sections = {
            "executive_summary": "",
            "local_climate_risk": "",
            "implications": "",
            "esg_opportunities": "",
            "verdict": "",
            "raw": full
        }

        text = full.strip()

        def extract(label):
            pat = rf"{label}[:\n]+(.*?)(\n[1-9]\)|\n[A-Z][A-Za-z ]+?:|\Z)"
            m = re.search(pat, text, flags=re.S|re.I)
            return m.group(1).strip() if m else ""

        sections["executive_summary"]    = extract("Executive Summary")
        sections["local_climate_risk"]   = extract("Local Climate Risk")
        sections["implications"]         = extract("Implications for Property Value & Insurability")
        sections["esg_opportunities"]    = extract("ESG & Resilience Opportunities")
        sections["verdict"]              = extract("Final Verdict")

        logging.info("Sections generated successfully")
        return sections
