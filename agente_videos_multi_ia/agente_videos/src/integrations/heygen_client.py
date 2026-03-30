import aiohttp
import asyncio
from typing import Dict, Any
from .base import BaseIntegration

class HeyGenIntegration(BaseIntegration):
    def _setup(self):
        self.api_key = self.config.get("apis", {}).get("heygen", {}).get("api_key")
        self.base_url = "https://api.heygen.com/v2"
        
        if not self.api_key:
            self.logger.warning("HeyGen API Key não configurada. Usando modo mock.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def generate_video(self, avatar_id: str, audio_url: str, background_url: str = None) -> str:
        """Gera um vídeo UGC-style usando HeyGen"""
        if not self.api_key:
            self.logger.info("Modo Mock: Simulando geração de vídeo HeyGen")
            return "mock_video_id_heygen"

        url = f"{self.base_url}/video/generate"
        
        # Configuração para parecer UGC (User Generated Content)
        data = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal" # Estilo casual
                    },
                    "voice": {
                        "type": "audio",
                        "audio_url": audio_url
                    },
                    "background": {
                        "type": "image",
                        "url": background_url
                    } if background_url else {"type": "color", "value": "#FFFFFF"}
                }
            ],
            "dimension": {
                "width": 1080,
                "height": 1920 # Formato Reels/TikTok
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erro HeyGen Submit ({response.status}): {error_text}")
                
                result = await response.json()
                return result.get("data", {}).get("video_id")

    async def wait_for_completion(self, video_id: str, timeout_seconds: int = 600) -> str:
        """Aguarda a conclusão do vídeo e retorna a URL final"""
        if not self.api_key:
            await asyncio.sleep(2)
            return "https://mock.url/heygen_ugc_video.mp4"

        url = f"{self.base_url}/video_status.get?video_id={video_id}"
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession() as session:
            while True:
                if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                    raise TimeoutError(f"Timeout aguardando vídeo HeyGen {video_id}")
                    
                async with session.get(url, headers=self._get_headers()) as response:
                    result = await response.json()
                    status = result.get("data", {}).get("status")
                    
                    if status == "completed":
                        return result.get("data", {}).get("video_url")
                    elif status in ["failed", "error"]:
                        raise Exception(f"Falha na geração do vídeo HeyGen {video_id}")
                        
                self.logger.debug(f"Vídeo {video_id} em processamento. Aguardando 15s...")
                await asyncio.sleep(15)
