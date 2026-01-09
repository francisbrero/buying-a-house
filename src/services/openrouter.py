"""OpenRouter API client for vision and text models."""

import base64
import os
from dataclasses import dataclass

import httpx


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API."""

    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    default_vision_model: str = "google/gemini-3-flash-preview"
    default_text_model: str = "google/gemini-3-flash-preview"
    site_url: str = "http://localhost"  # For OpenRouter rankings
    site_name: str = "House Evaluator"


class OpenRouterClient:
    """Client for OpenRouter API with vision support."""

    def __init__(self, config: OpenRouterConfig | None = None):
        if config is None:
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable required")
            config = OpenRouterConfig(api_key=api_key)

        self.config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "HTTP-Referer": config.site_url,
                "X-Title": config.site_name,
            },
            timeout=120.0,
        )

    def _make_request(self, messages: list[dict], model: str) -> str:
        """Make a chat completion request."""
        response = self._client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": messages,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        """Send a text chat request."""
        model = model or self.config.default_text_model
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self._make_request(messages, model)

    def vision(
        self,
        prompt: str,
        image_bytes: bytes,
        system_prompt: str | None = None,
        model: str | None = None,
        image_detail: str = "high",
    ) -> str:
        """Send a vision request with an image."""
        model = model or self.config.default_vision_model
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                        "detail": image_detail,
                    },
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        })

        return self._make_request(messages, model)

    def vision_with_json(
        self,
        prompt: str,
        image_bytes: bytes,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        """Vision request expecting JSON response."""
        full_prompt = f"{prompt}\n\nRespond with valid JSON only, no markdown."
        return self.vision(full_prompt, image_bytes, system_prompt, model)

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def get_openrouter_client() -> OpenRouterClient:
    """Get a configured OpenRouter client."""
    return OpenRouterClient()
