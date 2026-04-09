from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# Module toggles
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
TRIMMER_ENABLED = os.getenv("TRIMMER_ENABLED", "true").lower() == "true"
ROUTER_ENABLED = os.getenv("ROUTER_ENABLED", "true").lower() == "true"
LOGGER_ENABLED = os.getenv("LOGGER_ENABLED", "true").lower() == "true"

# Logger
LOG_OUTPUT_PATH = os.getenv("LOG_OUTPUT_PATH", "logs/session.html")

CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
CACHE_MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "1000"))