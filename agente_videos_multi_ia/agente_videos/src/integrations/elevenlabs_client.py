import aiohttp
import os
from typing import Dict, Any
from .base import BaseIntegration

class ElevenLabsIntegration(BaseIntegration):
    def _setup(self):
        self.api_key = self.config.get("apis", {}).get("elevenlabs", {}).get("api_key")
        self.model = self.config.get("apis", {}).get("elevenlabs", {}).get("model", "eleven_turbo_v2_5")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            self.logger.warning("ElevenLabs API Key não configurada. Usando modo mock.")

    async def generate_audio(self, text: str, voice_id: str, output_path: str) -> str:
        """Gera áudio a partir do texto e salva no disco"""
        if not self.api_key:
            self.logger.info("Modo Mock: Simulando geração de áudio")
            # Criar um arquivo vazio para simular
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write("mock audio content")
            return output_path

        url = f"{self.base_url}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        # Configuração otimizada para voz conversacional (UGC style)
        data = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": 0.35, # Menor estabilidade = mais emoção e variação natural
                "similarity_boost": 0.85,
                "style": 0.4, # Adiciona estilo conversacional
                "use_speaker_boost": True
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Erro ElevenLabs ({response.status}): {error_text}")
                    
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(await response.read())
                        
            self.logger.info(f"Áudio gerado com sucesso: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Erro ao gerar áudio: {str(e)}")
            raise
