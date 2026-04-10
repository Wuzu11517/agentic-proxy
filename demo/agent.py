import httpx
import asyncio

PROXY_URL = "http://localhost:8000/v1/messages"

HEADERS = {
    "content-type": "application/json",
    "anthropic-version": "2023-06-01",
}

MODEL = "claude-sonnet-4-6"

TURNS = [
    # --- SIMPLE: should route to Haiku ---
    "Summarize this in one sentence: The stock market rose today driven by strong earnings from tech companies.",
    "Translate this to Spanish: Good morning, how are you today?",
    "Format this as a bullet list: apples, oranges, bananas, grapes, watermelon.",
    "Extract the numbers from this sentence: I have 3 cats, 2 dogs, and 14 fish.",
    "Convert this to uppercase: hello world this is a test.",
    "Translate this to French: The weather is nice today.",
    "List the vowels in the English alphabet.",
    "What is the plural of 'cactus'?",
    "Translate 'thank you' into Japanese.",

    # --- MODERATE: should stay on Sonnet ---
    "Explain how binary search works and when you would use it over linear search.",
    "Write a short Python function that checks if a string is a palindrome.",
    "Review this code and suggest improvements: for i in range(len(arr)): print(arr[i])",
    "Explain the difference between REST and GraphQL APIs.",
    "Write a SQL query to find the top 5 customers by total order value.",
    "What are the tradeoffs between using a list vs a dictionary in Python?",
    "Explain what a closure is in JavaScript with a short example.",
    "What is the difference between TCP and UDP?",
    "Write a regex pattern to validate an email address.",

    # --- COMPLEX: should stay on Sonnet ---
    "Debug why a binary search tree might become unbalanced after repeated deletions and explain how AVL trees solve this.",
    "Design a system architecture for a distributed rate limiter that works across multiple servers with minimal latency.",
    "Explain how garbage collection works in the JVM and how it affects application performance under high load.",
    "What are the architectural tradeoffs between event sourcing and traditional CRUD database design for a financial system?",
    "How would you design a real-time collaborative text editor like Google Docs at scale?",

    # --- DUPLICATES: should all be cache hits ---
    "Summarize this in one sentence: The stock market rose today driven by strong earnings from tech companies.",
    "Translate this to Spanish: Good morning, how are you today?",
    "Explain how binary search works and when you would use it over linear search.",
    "Design a system architecture for a distributed rate limiter that works across multiple servers with minimal latency.",
    "Format this as a bullet list: apples, oranges, bananas, grapes, watermelon.",
    "Extract the numbers from this sentence: I have 3 cats, 2 dogs, and 14 fish.",
    "What are the tradeoffs between using a list vs a dictionary in Python?",
    "List the vowels in the English alphabet.",
    "Explain what a closure is in JavaScript with a short example.",
    "How would you design a real-time collaborative text editor like Google Docs at scale?",
]

SIMPLE_COUNT = 9
MODERATE_COUNT = 9
COMPLEX_COUNT = 5
DUPLICATE_START = SIMPLE_COUNT + MODERATE_COUNT + COMPLEX_COUNT


async def send_message(content: str) -> str:
    body = {
        "model": MODEL,
        "max_tokens": 150,
        "messages": [{"role": "user", "content": content}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(PROXY_URL, json=body, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]


async def main():
    print(f"Running demo agent — {len(TURNS)} total calls\n")
    print(f"  {SIMPLE_COUNT} simple | {MODERATE_COUNT} moderate | {COMPLEX_COUNT} complex | {len(TURNS) - DUPLICATE_START} duplicates\n")

    for i, prompt in enumerate(TURNS):
        tag = "DUPLICATE" if i >= DUPLICATE_START else f"Call {i + 1:02d}"
        print(f"[{tag}] {prompt[:80]}...")
        try:
            reply = await send_message(prompt)
            print(f"         {reply[:100]}...\n")
        except Exception as e:
            print(f"         ERROR: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())