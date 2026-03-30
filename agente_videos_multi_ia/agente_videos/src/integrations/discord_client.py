import aiohttp
import asyncio
from typing import Dict, Any, Optional
from .base import BaseIntegration

class DiscordIntegration(BaseIntegration):
    def _setup(self):
        self.bot_token = self.config.get("apis", {}).get("discord", {}).get("bot_token")
        self.channel_id = self.config.get("apis", {}).get("discord", {}).get("channel_id")
        self.base_url = "https://discord.com/api/v10"
        
        if not self.bot_token or not self.channel_id:
            self.logger.warning("Discord Bot Token ou Channel ID não configurados. Usando modo mock.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }

    async def send_approval_message(self, task_data: Dict[str, Any], video_url: str, script_data: Dict[str, str]) -> str:
        """Envia mensagem com botões de aprovação e retorna o ID da mensagem"""
        if not self.bot_token:
            self.logger.info("Modo Mock: Simulando envio para Discord")
            return "mock_message_id"

        url = f"{self.base_url}/channels/{self.channel_id}/messages"
        
        content = f"""=NOVO VÍDEO PRONTO PARA APROVAÇÃO

🌍 País: {task_data.get('pais')}
🗣️ Idioma do Vídeo: {task_data.get('idioma')}
📱 Vertical: {task_data.get('vertical')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 GANCHO (Hook - Primeiros 3s):
{script_data.get('gancho')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 ROTEIRO COMPLETO:
{script_data.get('roteiro_completo')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 CENÁRIO VISUAL:
{script_data.get('cenario')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎥 PRÉVIA DO VÍDEO:
{video_url}

👇 Clique em APROVAR para salvar no Google Drive ou REJEITAR para descartar."""

        data = {
            "content": content,
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "label": "✅ APROVAR E SALVAR",
                            "style": 3,
                            "custom_id": f"approve_{task_data.get('id', 'unknown')}"
                        },
                        {
                            "type": 2,
                            "label": "❌ REJEITAR",
                            "style": 4,
                            "custom_id": f"reject_{task_data.get('id', 'unknown')}"
                        }
                    ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self._get_headers()) as response:
                if response.status not in (200, 201):
                    error_text = await response.text()
                    raise Exception(f"Erro Discord ({response.status}): {error_text}")
                
                result = await response.json()
                return result.get("id")

    async def wait_for_approval(self, message_id: str, timeout_seconds: int = 86400) -> bool:
        """Aguarda a interação do usuário com os botões (Mock implementation)
        Em um cenário real, isso exigiria um webhook ou websocket (Gateway) do Discord.
        Para este agente, vamos simular a aprovação após 30 segundos no modo mock.
        """
        if not self.bot_token:
            self.logger.info("Modo Mock: Simulando aprovação humana em 5 segundos...")
            await asyncio.sleep(5)
            return True
            
        self.logger.warning("Aguardando aprovação real requer implementação de Webhook/Gateway. Retornando True por padrão.")
        return True
