from dotenv import load_dotenv
import os
import sys

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# Module toggles
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
TRIMMER_ENABLED = os.getenv("TRIMMER_ENABLED", "true").lower() == "true"
ROUTER_ENABLED = os.getenv("ROUTER_ENABLED", "true").lower() == "true"
LOGGER_ENABLED = os.getenv("LOGGER_ENABLED", "true").lower() == "true"

# Cache
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
CACHE_MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "1000"))


def validate():
    errors = []

    if not ANTHROPIC_API_KEY:
        errors.append("  - ANTHROPIC_API_KEY is missing. Add it to your .env file.")

    if CACHE_TTL_HOURS <= 0:
        errors.append("  - CACHE_TTL_HOURS must be greater than 0.")

    if CACHE_MAX_ENTRIES <= 0:
        errors.append("  - CACHE_MAX_ENTRIES must be greater than 0.")

    if errors:
        print("\n[agentic-proxy] Configuration errors found:\n")
        for e in errors:
            print(e)
        print("\nCopy .env.example to .env and fill in the required values.\n")
        sys.exit(1)

    print("[agentic-proxy] Config OK")


validate()