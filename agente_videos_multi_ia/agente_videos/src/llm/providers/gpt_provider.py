import aiohttp
from loguru import logger
from ..base_llm import BaseLLM

class GPTProvider(BaseLLM):
    def _setup(self):
        self.base_url = "https://api.openai.com/v1/chat/completions"
        if not self.api_key:
            logger.warning("OpenAI API Key não configurada. Usando modo mock.")

    async def _call_api(self, messages: list) -> str:
        if not self.api_key:
            return "Mock response from GPT"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model or "gpt-4-turbo",
            "messages": messages,
            "temperature": 0.7
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=data, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Erro OpenAI API: {error}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]

    async def generate_script(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self._call_api(messages)

    async def analyze_trend(self, country: str, vertical: str) -> str:
        prompt = f"Analise as tendências atuais para a vertical '{vertical}' no país '{country}'."
        return await self.generate_script(prompt)
