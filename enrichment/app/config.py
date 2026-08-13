import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BRIGHTDATA_API_TOKEN = os.getenv("BRIGHTDATA_API_TOKEN", "").strip()
BRIGHTDATA_UNLOCKER_ZONE = os.getenv("BRIGHTDATA_UNLOCKER_ZONE", "web_unlocker1").strip()
BRIGHTDATA_SERP_ZONE = os.getenv("BRIGHTDATA_SERP_ZONE", "serp_api1").strip()
BRIGHTDATA_ENDPOINT = "https://api.brightdata.com/request"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
LLM_MODEL = "claude-sonnet-5"

# Bedrock is the preferred path at an AWS event: it uses the AWS credentials
# already on the machine, so no separate API key is needed.
USE_BEDROCK = os.getenv("USE_BEDROCK", "").strip().lower() in ("1", "true", "yes")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1").strip()
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
).strip()


def _resolve_provider() -> str:
    if ANTHROPIC_API_KEY:
        return "anthropic"
    if USE_BEDROCK:
        return "bedrock"
    return "none"


LLM_PROVIDER = _resolve_provider()

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "21600"))
CACHE_DB = ROOT / "cache.db"

PORT = int(os.getenv("PORT", "8100"))

HAS_BRIGHTDATA = bool(BRIGHTDATA_API_TOKEN)
HAS_LLM = LLM_PROVIDER != "none"
