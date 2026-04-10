import httpx
import config

MODEL_TIERS = {
    "claude-opus-4-6": 3,
    "claude-sonnet-4-6": 2,
    "claude-haiku-4-5-20251001": 1,
}

TIER_TO_MODEL = {
    3: "claude-opus-4-6",
    2: "claude-sonnet-4-6",
    1: "claude-haiku-4-5-20251001",
}

TIER_TO_LABEL = {
    1: "SIMPLE",
    2: "MODERATE",
    3: "COMPLEX",
}

CLASSIFIER_MAX_CHARS = 500

CLASSIFIER_PROMPT = """Classify this prompt into one of three complexity tiers:

SIMPLE: formatting, summarizing, extracting, translating, listing
MODERATE: writing, explaining, reviewing, general reasoning, coding tasks
COMPLEX: debugging hard problems, architectural decisions, deep multi-step reasoning

Respond with only one word: SIMPLE, MODERATE, or COMPLEX.

Prompt: {prompt}"""


def _get_last_user_message(body: dict) -> str:
    messages = body.get("messages", [])
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str):
                return content
    return ""


def _complexity_to_tier(complexity: str) -> int:
    mapping = {
        "SIMPLE": 1,
        "MODERATE": 2,
        "COMPLEX": 3,
    }
    return mapping.get(complexity.strip().upper(), 2)


async def _classify_prompt(prompt: str) -> int:
    truncated = prompt[:CLASSIFIER_MAX_CHARS]

    body = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 5,
        "messages": [
            {
                "role": "user",
                "content": CLASSIFIER_PROMPT.format(prompt=truncated)
            }
        ]
    }

    headers = {
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            config.ANTHROPIC_API_URL,
            json=body,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        complexity = data["content"][0]["text"]
        return _complexity_to_tier(complexity)


async def route_model(body: dict) -> tuple[dict, str | None]:
    requested_model = body.get("model", "")
    requested_tier = MODEL_TIERS.get(requested_model)

    # If model is not in our tier list or already Haiku, skip routing
    if requested_tier is None or requested_tier == 1:
        return body, None

    prompt = _get_last_user_message(body)
    if not prompt:
        return body, None

    complexity_tier = await _classify_prompt(prompt)
    complexity_label = TIER_TO_LABEL[complexity_tier]

    # Only downgrade, never upgrade
    if complexity_tier < requested_tier:
        routed_model = TIER_TO_MODEL[complexity_tier]
        body = {**body, "model": routed_model}

    return body, complexity_label