import os
import json
import httpx
from typing import AsyncGenerator

class CloudAIProvider:
    """
    Unified Cloud AI Provider supporting Google Gemini API, OpenAI/Groq,
    and optional local Ollama. Cloud-native & Serverless friendly (Render & Vercel ready).
    """

    def __init__(self):
        # 1. Google Gemini API Config (Primary choice for Render / Vercel deployment)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        # 2. OpenAI / Groq API Config (Alternative Cloud LLM options)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        self.openai_base_url = os.getenv(
            "OPENAI_BASE_URL",
            "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else "https://api.openai.com/v1"
        )
        self.openai_model = os.getenv(
            "OPENAI_MODEL",
            "llama-3.1-8b-instant" if os.getenv("GROQ_API_KEY") else "gpt-4o-mini"
        )

        # 3. Optional Local Ollama (Priority 3 - local development only)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("LLM_MODEL", "llama3")

    async def is_available(self) -> bool:
        """Returns True if any cloud API key or local daemon is active."""
        if self.gemini_api_key or self.openai_api_key:
            return True

        if os.getenv("ENABLE_LOCAL_OLLAMA") == "true":
            try:
                async with httpx.AsyncClient(timeout=1.5) as client:
                    res = await client.get(f"{self.ollama_base_url}/api/tags")
                    return res.status_code == 200
            except Exception:
                return False

        return False

    async def generate(self, prompt: str) -> str:
        """Generates a complete response from the configured cloud/local provider."""
        if self.gemini_api_key:
            return await self._generate_gemini(prompt)

        if self.openai_api_key:
            return await self._generate_openai(prompt)

        return await self._generate_ollama(prompt)

    async def stream_generate(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams tokens from the configured provider as an async generator."""
        if self.gemini_api_key:
            async for token in self._stream_gemini(prompt):
                yield token
        elif self.openai_api_key:
            async for token in self._stream_openai(prompt):
                yield token
        else:
            async for token in self._stream_ollama(prompt):
                yield token

    # --- GOOGLE GEMINI API (HTTPX Client, Zero-SDK dependency) ---
    async def _generate_gemini(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
        except Exception as e:
            return f"Gemini API Error: {str(e)}"

    async def _stream_gemini(self, prompt: str) -> AsyncGenerator[str, None]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:streamGenerateContent?alt=sse&key={self.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        yield f"Gemini Error: HTTP {response.status_code}"
                        return
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            raw_json = line[6:].strip()
                            if raw_json:
                                try:
                                    chunk = json.loads(raw_json)
                                    candidates = chunk.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        for p in parts:
                                            text = p.get("text", "")
                                            if text:
                                                yield text
                                except Exception:
                                    continue
        except Exception as e:
            yield f"Gemini Stream Error: {str(e)}"

    # --- OPENAI / GROQ API ---
    async def _generate_openai(self, prompt: str) -> str:
        url = f"{self.openai_base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.openai_model,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Cloud LLM Error: {str(e)}"

    async def _stream_openai(self, prompt: str) -> AsyncGenerator[str, None]:
        url = f"{self.openai_base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            raw = line[6:].strip()
                            if raw == "[DONE]":
                                break
                            try:
                                chunk = json.loads(raw)
                                delta = chunk["choices"][0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    yield token
                            except Exception:
                                continue
        except Exception as e:
            yield f"Cloud LLM Stream Error: {str(e)}"

    # --- LOCAL OLLAMA (DEV ONLY) ---
    async def _generate_ollama(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={"model": self.ollama_model, "prompt": prompt, "stream": False}
                )
                res.raise_for_status()
                return res.json().get("response", "")
        except Exception as e:
            return f"Ollama Error: {str(e)}"

    async def _stream_ollama(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_base_url}/api/generate",
                    json={"model": self.ollama_model, "prompt": prompt, "stream": True}
                ) as response:
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
            yield f"Ollama Error: {str(e)}"

# Alias for backward compatibility across existing routes and tests
OllamaProvider = CloudAIProvider
