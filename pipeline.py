import config
from proxy import forward_request

# Each module will be imported here as we build them
# from cache import check_cache, store_cache
# from trimmer import trim_context
# from router import route_model
# from logger import log_request


async def run_pipeline(body: dict, headers: dict) -> dict:
    meta = {
        "cache_hit": False,
        "original_model": body.get("model"),
        "routed_model": None,
        "original_message_count": len(body.get("messages", [])),
        "trimmed_message_count": None,
    }

    # Step 1: Cache check
    if config.CACHE_ENABLED:
        pass  # result = check_cache(body)
        # if result:
        #     meta["cache_hit"] = True
        #     if config.LOGGER_ENABLED:
        #         log_request(body, result, meta)
        #     return result

    # Step 2: Context trimming
    if config.TRIMMER_ENABLED:
        pass  # body = trim_context(body)
        # meta["trimmed_message_count"] = len(body.get("messages", []))

    # Step 3: Model routing
    if config.ROUTER_ENABLED:
        pass  # body = route_model(body)
        # meta["routed_model"] = body.get("model")

    # Step 4: Forward to Anthropic API
    result = await forward_request(body, headers)

    # Step 5: Store in cache
    if config.CACHE_ENABLED:
        pass  # store_cache(body, result)

    # Step 6: Log the request
    if config.LOGGER_ENABLED:
        pass  # log_request(body, result, meta)

    return result