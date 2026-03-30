import aiohttp
import asyncio
from typing import Dict, Any, Optional
from .base import BaseIntegration

class TopviewIntegration(BaseIntegration):
    def _setup(self):
        self.api_key = self.config.get("apis", {}).get("topview", {}).get("api_key")
        self.uid = self.config.get("apis", {}).get("topview", {}).get("uid")
        self.base_url = "https://api.topview.ai/v1"
        
        if not self.api_key or not self.uid:
            self.logger.warning("Topview API Key ou UID não configurados. Usando modo mock.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Topview-Uid": self.uid,
            "Content-Type": "application/json"
        }

    async def submit_task(self, text: str, avatar_id: str, audio_url: str) -> str:
        """Submete uma tarefa de geração de vídeo e retorna o taskId"""
        if not self.api_key:
            self.logger.info("Modo Mock: Simulando submissão de vídeo")
            return "mock_task_id_123"

        url = f"{self.base_url}/video_process/task/submit"
        data = {
            "text": text,
            "avatarId": avatar_id,
            "audioUrl": audio_url
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erro Topview Submit ({response.status}): {error_text}")
                
                result = await response.json()
                return result.get("data", {}).get("taskId")

    async def query_task(self, task_id: str) -> Dict[str, Any]:
        """Consulta o status de uma tarefa"""
        if not self.api_key:
            return {"status": "completed", "previewUrl": "https://mock.url/preview.mp4"}

        url = f"{self.base_url}/video_process/task/query?taskId={task_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erro Topview Query ({response.status}): {error_text}")
                
                result = await response.json()
                return result.get("data", {})

    async def wait_for_completion(self, task_id: str, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Aguarda até que o vídeo seja concluído"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                raise TimeoutError(f"Timeout aguardando vídeo {task_id}")
                
            task_data = await self.query_task(task_id)
            status = task_data.get("status")
            
            if status == "completed":
                return task_data
            elif status == "failed":
                raise Exception(f"Falha na geração do vídeo {task_id}")
                
            self.logger.debug(f"Vídeo {task_id} em processamento. Aguardando 10s...")
            await asyncio.sleep(10)

    async def export_video(self, task_id: str, quality: str = "1080p") -> str:
        """Exporta o vídeo em alta qualidade e retorna a URL final"""
        if not self.api_key:
            return "https://mock.url/final_video.mp4"

        url = f"{self.base_url}/video_process/task/export"
        data = {
            "taskId": task_id,
            "quality": quality
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erro Topview Export ({response.status}): {error_text}")
                
                result = await response.json()
                return result.get("data", {}).get("videoUrl")
