import httpx
import time
import config


async def forward_request(body: dict, headers: dict) -> tuple[dict, float]:
    forward_headers = {
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": headers.get("anthropic-version", "2023-06-01"),
        "content-type": "application/json",
    }

    start = time.monotonic()

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            config.ANTHROPIC_API_URL,
            json=body,
            headers=forward_headers,
        )
        response.raise_for_status()

    latency_ms = round((time.monotonic() - start) * 1000)
    return response.json(), latency_ms