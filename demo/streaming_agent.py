import httpx
import asyncio
import json

PROXY_URL = "http://localhost:8000/v1/messages"

HEADERS = {
    "content-type": "application/json",
    "anthropic-version": "2023-06-01",
}

MODEL = "claude-sonnet-4-6"

PROMPTS = [
    "Write a short poem about the ocean.",
    "Explain how a computer works in 3 sentences.",
    # Duplicate — should stream from cache
    "Write a short poem about the ocean.",
]


async def stream_message(content: str):
    body = {
        "model": MODEL,
        "max_tokens": 150,
        "stream": True,
        "messages": [{"role": "user", "content": content}],
    }

    print(f"Prompt: {content[:60]}...")
    print("Response: ", end="", flush=True)

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", PROXY_URL, json=body, headers=HEADERS) as response:
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                raw = line[6:]
                if raw == "[DONE]":
                    break
                try:
                    event = json.loads(raw)
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            print(delta.get("text", ""), end="", flush=True)
                except json.JSONDecodeError:
                    pass

    print("\n")


async def main():
    print("Running streaming demo agent...\n")
    for prompt in PROMPTS:
        await stream_message(prompt)


if __name__ == "__main__":
    asyncio.run(main())