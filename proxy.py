import httpx
import time
import json
import config


class ProxyError(Exception):
    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


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


async def stream_request(body: dict, headers: dict):
    """
    Yields raw SSE chunks to the caller while buffering the full response.
    Returns via StopAsyncIteration with a (reconstructed_response, latency_ms) tuple
    stored on the generator so pipeline.py can retrieve it after exhausting the stream.
    """
    forward_headers = {
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": headers.get("anthropic-version", "2023-06-01"),
        "content-type": "application/json",
    }

    start = time.monotonic()
    buffer = []
    input_tokens = 0
    output_tokens = 0
    full_text = ""
    model = body.get("model", "")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                config.ANTHROPIC_API_URL,
                json=body,
                headers=forward_headers,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # Forward raw line immediately to the agent
                    yield line + "\n\n"

                    # Parse and buffer for cache/logger
                    if line.startswith("data: "):
                        raw = line[6:]
                        if raw == "[DONE]":
                            continue
                        try:
                            event = json.loads(raw)
                            buffer.append(event)

                            # Collect text deltas
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    full_text += delta.get("text", "")

                            # Capture token counts from final event
                            if event.get("type") == "message_delta":
                                usage = event.get("usage", {})
                                output_tokens = usage.get("output_tokens", 0)

                            if event.get("type") == "message_start":
                                message = event.get("message", {})
                                usage = message.get("usage", {})
                                input_tokens = usage.get("input_tokens", 0)

                        except json.JSONDecodeError:
                            pass

    except httpx.TimeoutException:
        raise ProxyError(408, "Streaming request to Anthropic API timed out.")
    except httpx.HTTPStatusError as e:
        raise ProxyError(e.response.status_code, {"error": e.response.text})
    except httpx.RequestError as e:
        raise ProxyError(503, f"Could not reach Anthropic API: {str(e)}")

    latency_ms = round((time.monotonic() - start) * 1000)

    # Reconstruct a response object that matches the non-streaming format
    # so cache and logger can handle it the same way
    reconstructed = {
        "id": next((e.get("message", {}).get("id") for e in buffer if e.get("type") == "message_start"), ""),
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": full_text}],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
    }

    # Store on generator so pipeline can retrieve after stream ends
    stream_request._last_result = (reconstructed, latency_ms)