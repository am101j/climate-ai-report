import os
import json
from dotenv import load_dotenv
from services.ai_writer import AIWriter

# Load variables from .env
load_dotenv()

# Mock data for testing
mock_data = {
    "lat": 48.097,
    "lon": 11.506,
    "risk_score": {
        "scores": {
            "air_quality": 3.4,
            "flood_risk": 1.2,
            "wildfire_risk": 0.5
        }
    },
    "flood_zone": {"flood_zone": "X"},
    "wildfire_now": {"properties": {"fire_risk_class": "Low"}},
    "wildfire_ts": {},
    "aq_daily": {},
    "aq_monthly": {},
    "heatwind_daily": {},
    "heatwind_ts": {}
}

def test_ai_writer():
    print("🧪 Running AIWriter test...")
    try:
        # This requires a live call to OpenAI, ensure API key is set
        ai_writer = AIWriter(openai_api_key=os.environ.get("OPENAI_API_KEY"))
        narrative_json = ai_writer.generate_sections(**mock_data)

        # 1. Check if the output is a dictionary
        assert isinstance(narrative_json, dict)
        print("✅ Output is a dictionary.")

        # 2. Check for top-level keys
        required_keys = ["executive_summary", "market_analysis", "climate_and_esg_risks", "final_verdict"]
        for key in required_keys:
            assert key in narrative_json
        print(f"✅ All required top-level keys found: {required_keys}")

        # 3. Check schema of a section
        summary_section = narrative_json["executive_summary"]
        assert "title" in summary_section
        assert "subsections" in summary_section
        assert isinstance(summary_section["subsections"], list)
        print("✅ Executive Summary has correct basic schema.")
        
        print("\n🎉 AI Writer test passed! 🎉")
        print("\nSample Output (Executive Summary Title):", summary_section.get("title"))
        print("Sample Output (First Subsection Subtitle):", summary_section["subsections"][0].get("subtitle") if summary_section["subsections"] else "N/A")

    except Exception as e:
        print(f"❌ AI Writer test failed: {e}")

if __name__ == "__main__":
    test_ai_writer()