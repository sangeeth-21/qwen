import json
from typing import AsyncGenerator

import httpx

from app.backend.config import settings

SYSTEM_PROMPT = (
    "You are Qwen, a friendly voice assistant. "
    "Keep responses very concise - 1 to 3 sentences. "
    "Speak naturally and conversationally."
)


def _build_url() -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.google_model}:streamGenerateContent"
        f"?alt=sse&key={settings.google_api_key}"
    )


async def chat_stream(messages: list[dict]) -> AsyncGenerator[str, None]:
    if not settings.google_api_key:
        yield "Please set your Google AI Studio API key in settings."
        return

    contents = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
        {"role": "model", "parts": [{"text": "Got it. I'll keep it short."}]},
    ]
    for m in messages:
        role = "user" if m["role"] in ("user", "system") else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {"contents": contents}

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", _build_url(), json=payload) as resp:
            if resp.status_code in (403, 401):
                yield "Invalid API key. Please check your Google AI Studio key."
                return
            if resp.status_code == 429:
                yield "I'm being rate-limited. Please wait a moment."
                return
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    for c in chunk.get("candidates", []):
                        for part in c.get("content", {}).get("parts", []):
                            yield part.get("text", "")
                except json.JSONDecodeError:
                    pass


async def chat(messages: list[dict]) -> str:
    parts = []
    async for chunk in chat_stream(messages):
        parts.append(chunk)
    return "".join(parts)
