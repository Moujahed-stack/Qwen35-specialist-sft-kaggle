import time
from typing import Optional

import httpx


class ChatClient:
    # Any OpenAI-compatible /chat/completions endpoint: OpenRouter, Together, Fireworks, DeepSeek,
    # vLLM, Ollama (http://localhost:11434/v1), a Hugging Face endpoint, etc.

    def __init__(self, model: str, base_url: str, api_key: str = "",
                 extra_body: Optional[dict] = None, timeout: float = 300.0, retries: int = 5):
        self.model = model
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self.extra_body = extra_body or {}
        self.timeout = timeout
        self.retries = retries

    def generate(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 2048) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        payload.update(self.extra_body)
        last = None
        for attempt in range(self.retries):
            try:
                r = httpx.post(self.url, headers=self.headers, json=payload, timeout=self.timeout)
                if r.status_code in (429, 500, 502, 503, 504):
                    last = f"HTTP {r.status_code}: {r.text[:200]}"
                else:
                    r.raise_for_status()
                    return r.json()["choices"][0]["message"].get("content") or ""
            except (httpx.TransportError, httpx.HTTPStatusError, KeyError, ValueError) as e:
                last = repr(e)
            time.sleep(min(2 ** attempt, 30))
        raise RuntimeError(f"generation failed after {self.retries} attempts: {last}")
