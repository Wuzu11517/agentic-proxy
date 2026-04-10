import config
from proxy import forward_request
from modules.cache import check_cache, store_cache
from modules.router import route_model
from modules.logger import log_request, estimate_cost


async def run_pipeline(body: dict, headers: dict) -> dict:
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
            # For cache hits, original_cost is what we would have paid
            # actual_cost is 0 since we never hit the API
            usage = result.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            meta["original_cost"] = estimate_cost(meta["original_model"], input_tokens, output_tokens)
            meta["actual_cost"] = 0.0
            if config.LOGGER_ENABLED:
                log_request(body, result, meta)
            return result

    # Snapshot original body before any modifications for consistent cache keying
    original_body = body

    # Step 2: Context trimming (not yet implemented)

    # Step 3: Model routing
    final_model = meta["original_model"]
    if config.ROUTER_ENABLED:
        try:
            import time
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

    # Step 5: Calculate costs explicitly
    # actual_cost  = what we paid (using final routed model)
    # original_cost = what we would have paid (using original model)
    usage = result.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    meta["actual_cost"] = estimate_cost(final_model, input_tokens, output_tokens)
    meta["original_cost"] = estimate_cost(meta["original_model"], input_tokens, output_tokens)

    # Step 6: Store in cache using original body as key
    if config.CACHE_ENABLED:
        store_cache(original_body, result)

    # Step 7: Log the request
    if config.LOGGER_ENABLED:
        log_request(body, result, meta)

    return result