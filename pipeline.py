import time
import config
from proxy import forward_request, stream_request
from modules.cache import check_cache, store_cache
from modules.router import route_model
from modules.logger import log_request, estimate_cost


async def run_pipeline(body: dict, headers: dict) -> dict:
    is_streaming = body.get("stream", False)

    if is_streaming:
        return await _streaming_pipeline(body, headers)
    return await _standard_pipeline(body, headers)


async def _standard_pipeline(body: dict, headers: dict) -> dict:
    meta = {
        "cache_hit": False,
        "original_model": body.get("model"),
        "routed_model": None,
        "complexity": None,
        "routing_decision": "skipped",
        "original_message_count": len(body.get("messages", [])),
        "trimmed_message_count": None,
        "latency_ms": 0,
        "router_latency_ms": 0,
        "original_cost": None,
        "actual_cost": None,
    }

    # Step 1: Cache check
    if config.CACHE_ENABLED:
        result = check_cache(body)
        if result:
            meta["cache_hit"] = True
            meta["latency_ms"] = 0
            usage = result.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            meta["original_cost"] = estimate_cost(meta["original_model"], input_tokens, output_tokens)
            meta["actual_cost"] = 0.0
            if config.LOGGER_ENABLED:
                log_request(body, result, meta)
            return result

    original_body = body

    # Step 2: Context trimming (not yet implemented)

    # Step 3: Model routing
    final_model = meta["original_model"]
    if config.ROUTER_ENABLED:
        try:
            router_start = time.monotonic()
            body, complexity_label = await route_model(body)
            meta["router_latency_ms"] = round((time.monotonic() - router_start) * 1000)
            meta["complexity"] = complexity_label
            final_model = body.get("model")
            if final_model != meta["original_model"]:
                meta["routed_model"] = final_model
                meta["routing_decision"] = "downgraded"
            else:
                meta["routing_decision"] = "kept"
        except Exception as e:
            print(f"[agentic-proxy] Router failed, using original model: {e}")
            meta["routing_decision"] = "skipped"

    # Step 4: Forward to Anthropic API
    result, latency_ms = await forward_request(body, headers)
    meta["latency_ms"] = latency_ms

    # Step 5: Calculate costs
    usage = result.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    meta["actual_cost"] = estimate_cost(final_model, input_tokens, output_tokens)
    meta["original_cost"] = estimate_cost(meta["original_model"], input_tokens, output_tokens)

    # Step 6: Store in cache
    if config.CACHE_ENABLED:
        store_cache(original_body, result)

    # Step 7: Log
    if config.LOGGER_ENABLED:
        log_request(body, result, meta)

    return result


async def _streaming_pipeline(body: dict, headers: dict):
    """
    Returns an async generator that yields SSE chunks to the caller.
    Cache check happens before streaming starts.
    Cache store and logging happen after the stream ends.
    """
    meta = {
        "cache_hit": False,
        "original_model": body.get("model"),
        "routed_model": None,
        "complexity": None,
        "routing_decision": "skipped",
        "original_message_count": len(body.get("messages", [])),
        "trimmed_message_count": None,
        "latency_ms": 0,
        "router_latency_ms": 0,
        "original_cost": None,
        "actual_cost": None,
    }

    # Step 1: Cache check — serve cached response as a fake stream
    if config.CACHE_ENABLED:
        cached = check_cache(body)
        if cached:
            meta["cache_hit"] = True
            usage = cached.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            meta["original_cost"] = estimate_cost(meta["original_model"], input_tokens, output_tokens)
            meta["actual_cost"] = 0.0
            if config.LOGGER_ENABLED:
                log_request(body, cached, meta)
            return _replay_cached_stream(cached)

    original_body = body

    # Step 2: Model routing
    final_model = meta["original_model"]
    if config.ROUTER_ENABLED:
        try:
            router_start = time.monotonic()
            body, complexity_label = await route_model(body)
            meta["router_latency_ms"] = round((time.monotonic() - router_start) * 1000)
            meta["complexity"] = complexity_label
            final_model = body.get("model")
            if final_model != meta["original_model"]:
                meta["routed_model"] = final_model
                meta["routing_decision"] = "downgraded"
            else:
                meta["routing_decision"] = "kept"
        except Exception as e:
            print(f"[agentic-proxy] Router failed, using original model: {e}")
            meta["routing_decision"] = "skipped"

    # Step 3: Stream from Anthropic, collect result after
    return _run_stream(body, headers, original_body, meta, final_model)


async def _run_stream(body, headers, original_body, meta, final_model):
    """Yields chunks while collecting result for cache and logger."""
    import json as json_module

    gen = stream_request(body, headers)

    async for chunk in gen:
        yield chunk

    # After stream ends, retrieve the reconstructed result
    result, latency_ms = stream_request._last_result
    meta["latency_ms"] = latency_ms

    usage = result.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    meta["actual_cost"] = estimate_cost(final_model, input_tokens, output_tokens)
    meta["original_cost"] = estimate_cost(meta["original_model"], input_tokens, output_tokens)

    if config.CACHE_ENABLED:
        store_cache(original_body, result)

    if config.LOGGER_ENABLED:
        log_request(body, result, meta)


async def _replay_cached_stream(cached: dict):
    """Replays a cached response as SSE events."""
    import json as json_module
    import asyncio

    text = ""
    content = cached.get("content", [])
    if content and content[0].get("type") == "text":
        text = content[0].get("text", "")

    # message_start
    start_event = {
        "type": "message_start",
        "message": {
            "id": cached.get("id", ""),
            "type": "message",
            "role": "assistant",
            "model": cached.get("model", ""),
            "usage": cached.get("usage", {}),
            "content": [],
        }
    }
    yield f"data: {json_module.dumps(start_event)}\n\n"

    # content_block_start
    yield f'data: {{"type": "content_block_start", "index": 0, "content_block": {{"type": "text", "text": ""}}}}\n\n'

    # Send text in small chunks to simulate streaming
    chunk_size = 20
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        delta_event = {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": chunk}
        }
        yield f"data: {json_module.dumps(delta_event)}\n\n"
        await asyncio.sleep(0)

    # content_block_stop
    yield f'data: {{"type": "content_block_stop", "index": 0}}\n\n'

    # message_delta with usage
    delta_event = {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn"},
        "usage": {"output_tokens": cached.get("usage", {}).get("output_tokens", 0)}
    }
    yield f"data: {json_module.dumps(delta_event)}\n\n"

    # message_stop
    yield f'data: {{"type": "message_stop"}}\n\n'
    yield "data: [DONE]\n\n"