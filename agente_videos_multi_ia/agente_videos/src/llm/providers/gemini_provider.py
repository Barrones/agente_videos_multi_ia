import aiohttp
from loguru import logger
from ..base_llm import BaseLLM

class GeminiProvider(BaseLLM):
    def _setup(self):
        self.model_name = self.model or "gemini-2.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        if not self.api_key:
            logger.warning("Google Gemini API Key não configurada. Usando modo mock.")

    async def _call_api(self, prompt: str, system_prompt: str = None) -> str:
        if not self.api_key:
            return "Mock response from Gemini"

        url = f"{self.base_url}?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Gemini structure
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}\n\nUser: {prompt}"}]})
        else:
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            
        data = {
            "contents": contents
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Erro Gemini API: {error}")
                
                result = await response.json()
                try:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return "Erro ao parsear resposta do Gemini"

    async def generate_script(self, prompt: str, system_prompt: str = None) -> str:
        return await self._call_api(prompt, system_prompt)

    async def analyze_trend(self, country: str, vertical: str) -> str:
        prompt = f"Analise as tendências atuais para a vertical '{vertical}' no país '{country}'."
        return await self.generate_script(prompt)
