"""
OpenRouter LLM adapter — provides access to frontier models via OpenRouter API.

Working models tested:
- google/gemma-4-26b-a4b-it:free (free, works for structured extraction)
- meta-llama/llama-3.3-70b-instruct (paid, cheap, good quality)

Models blocked in this region:
- anthropic/claude-* (403 region restriction)
- openai/gpt-* (403 region restriction)

This adapter replaces the z-ai CLI which was rate-limited.
"""
import json
import os
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"


def chat(prompt: str, system: str = None, model: str = None, max_tokens: int = 500, temperature: float = 0.3) -> Optional[Dict[str, Any]]:
    """Call OpenRouter chat completion API.

    Returns the full response dict, or None on failure.
    """
    model = model or DEFAULT_MODEL
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://discovery-fabric.local",
            "X-Title": "Discovery Evidence Fabric",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read())
            return {"error": err.get("error", {}).get("message", str(e))}
        except:
            return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:100]}"}


def chat_text(prompt: str, system: str = None, model: str = None, max_tokens: int = 500) -> Optional[str]:
    """Call OpenRouter and return just the content text."""
    result = chat(prompt, system, model, max_tokens)
    if result and "error" not in result:
        return result["choices"][0]["message"]["content"]
    return None


def chat_json(prompt: str, system: str = None, model: str = None, max_tokens: int = 500) -> Optional[dict]:
    """Call OpenRouter and parse the response as JSON."""
    text = chat_text(prompt, system, model, max_tokens)
    if not text:
        return None
    # Strip markdown fences
    text = text.strip().strip("`").strip()
    if text.startswith("json"):
        text = text[4:].strip()
    # Find first { and last }
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        text = text[first:last+1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


if __name__ == "__main__":
    # Test
    print("=== Test 1: Simple chat ===")
    result = chat_text("Say hello")
    print(f"  Result: {result[:100] if result else 'FAILED'}")

    print("\n=== Test 2: JSON extraction ===")
    result = chat_json(
        'Extract from: "We show a battery reaching 300Wh/kg using silicon anode." Output JSON: {"objective":"","input":"","output":""}',
        system="Output only JSON, no markdown."
    )
    print(f"  Result: {result}")
