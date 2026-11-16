import os
import json
import httpx
from typing import AsyncGenerator

class OllamaProvider:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "llama3")

    async def is_available(self) -> bool:
        """Checks if Ollama service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str) -> str:
        """Generates a complete response from Ollama."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                return f"AI Error: {str(e)}"

    async def stream_generate(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams tokens from Ollama as an async generator."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": True}
                ) as response:
                    if response.status_code != 200:
                        yield f"AI Error: HTTP {response.status_code}"
                        return
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                token = chunk.get("response", "")
                                if token:
                                    yield token
                                if chunk.get("done", False):
                                    break
                            except Exception:
                                continue
        except Exception as e:
            yield f"AI Error: {str(e)}"
