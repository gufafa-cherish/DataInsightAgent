import os
from pathlib import Path


AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

AB_DATA_PATH = DATA_DIR / "ab_data.csv"
REFUND_DATA_PATH = DATA_DIR / "refund_detail_generated.csv"
AB_DASHBOARD_PATH = OUTPUT_DIR / "ab_test_dashboard.html"
REFUND_DASHBOARD_PATH = OUTPUT_DIR / "refund_anomaly_dashboard.html"
SUMMARY_PATH = OUTPUT_DIR / "analysis_summary.json"
AB_SUMMARY_PATH = OUTPUT_DIR / "ab_analysis_summary.json"
REFUND_SUMMARY_PATH = OUTPUT_DIR / "refund_analysis_summary.json"
LAST_AGENT_RESULT_PATH = OUTPUT_DIR / "agent_last_result.json"
SIGNIFICANCE_LEVEL = 0.05

DEFAULT_MODEL = os.getenv(
    "DATA_INSIGHT_MODEL",
    os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
)
DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL") or None
AGENT_RECURSION_LIMIT = int(os.getenv("DATA_INSIGHT_RECURSION_LIMIT", "20"))
