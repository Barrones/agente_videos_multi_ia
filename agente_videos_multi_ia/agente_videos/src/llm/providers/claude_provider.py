import aiohttp
from loguru import logger
from ..base_llm import BaseLLM

class ClaudeProvider(BaseLLM):
    def _setup(self):
        self.base_url = "https://api.anthropic.com/v1/messages"
        if not self.api_key:
            logger.warning("Anthropic API Key não configurada. Usando modo mock.")

    async def _call_api(self, prompt: str, system_prompt: str = None) -> str:
        if not self.api_key:
            return "Mock response from Claude"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model or "claude-3-5-sonnet-20240620",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        if system_prompt:
            data["system"] = system_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=data, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Erro Anthropic API: {error}")
                
                result = await response.json()
                return result["content"][0]["text"]

    async def generate_script(self, prompt: str, system_prompt: str = None) -> str:
        return await self._call_api(prompt, system_prompt)

    async def analyze_trend(self, country: str, vertical: str) -> str:
        prompt = f"Analise as tendências atuais para a vertical '{vertical}' no país '{country}'."
        return await self.generate_script(prompt)
