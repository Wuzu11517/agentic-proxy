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

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                config.ANTHROPIC_API_URL,
                json=body,
                headers=forward_headers,
            )
            latency_ms = round((time.monotonic() - start) * 1000)
            response.raise_for_status()
            return response.json(), latency_ms

    except httpx.TimeoutException:
        raise ProxyError(408, "Request to Anthropic API timed out.")

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        try:
            detail = e.response.json()
        except Exception:
            detail = {"error": e.response.text}
        raise ProxyError(status, detail)

    except httpx.RequestError as e:
        raise ProxyError(503, f"Could not reach Anthropic API: {str(e)}")


class ProxyError(Exception):
    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))