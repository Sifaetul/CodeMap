import os
import httpx

class OllamaProvider:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "llama3")

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                return f"AI Error: {str(e)}"
