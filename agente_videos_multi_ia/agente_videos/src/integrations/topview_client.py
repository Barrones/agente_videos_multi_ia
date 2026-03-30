import aiohttp
import asyncio
from typing import Dict, Any, Optional
from .base import BaseIntegration
from src.api.server import update_topview_task
from src.utils.retry import with_retry

class TopviewIntegration(BaseIntegration):
    def _setup(self):
        self.api_key = self.config.get("apis", {}).get("topview", {}).get("api_key")
        self.uid = self.config.get("apis", {}).get("topview", {}).get("uid")
        self.base_url = "https://api.topview.ai/v1"
        
        if not self.api_key or not self.uid:
            self.logger.warning("Topview API Key ou UID não configurados. Usando modo mock.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}" if not self.api_key.startswith("Bearer ") else self.api_key,
            "Topview-Uid": self.uid,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @with_retry(max_attempts=3)
    async def submit_task(self, script: str, avatar_id: str = None, voice_id: str = None, image_url: str = None, language: str = "en") -> str:
        """Submete uma tarefa de geração de vídeo usando Avatar Marketing Video API"""
        if not self.api_key:
            self.logger.info("Modo Mock: Simulando submissão de vídeo Avatar Marketing")
            return "mock_task_id_123"

        url = f"{self.base_url}/m2v/task/submit"
        
        # Configuração para UGC
        payload = {
            "isDiyScript": "true",
            "diyScriptDescription": script,
            "aspectRatio": "9:16",
            "language": language,
            "videoLengthType": 1, # 30-50s
            "preview": "false" # Queremos o vídeo final
        }
        
        if avatar_id:
            payload["aiavatarId"] = avatar_id
        if voice_id:
            payload["voiceId"] = voice_id
            
        if image_url:
            payload["productLink"] = image_url
        else:
            payload["productLink"] = "https://www.amazon.com/dp/B0CXVSRY56" # Fallback

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erro Topview Submit ({response.status}): {error_text}")
                
                result = await response.json()
                if result.get("code") != 200:
                    raise Exception(f"Erro na API Topview: {result}")
                    
                return result.get("data", {}).get("taskId")

    @with_retry(max_attempts=3)
    async def query_task(self, task_id: str) -> Dict[str, Any]:
        """Consulta o status de uma tarefa"""
        if not self.api_key:
            return {"status": 3, "videoUrl": "https://mock.url/final_video.mp4"}

        url = f"{self.base_url}/m2v/task/query?taskId={task_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erro Topview Query ({response.status}): {error_text}")
                
                result = await response.json()
                if result.get("code") != 200:
                    raise Exception(f"Erro na API Topview: {result}")
                    
                return result.get("data", {})

    async def wait_for_completion(self, task_id: str, timeout_seconds: int = 600) -> Dict[str, Any]:
        """Aguarda até que o vídeo seja concluído (polling inteligente)"""
        start_time = asyncio.get_event_loop().time()
        
        status_map = {
            1: "Pendente",
            2: "Processando",
            3: "Concluído",
            4: "Falhou"
        }
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                update_topview_task(task_id, "Timeout", "Tempo limite excedido")
                raise TimeoutError(f"Timeout aguardando vídeo {task_id}")
                
            task_data = await self.query_task(task_id)
            status = task_data.get("status")
            status_text = status_map.get(status, f"Desconhecido ({status})")
            
            update_topview_task(task_id, status_text, f"Progresso: {task_data.get('progress', 0)}%")
            
            # Status: 1=pending, 2=processing, 3=completed, 4=failed
            if status == 3:
                return task_data
            elif status == 4:
                raise Exception(f"Falha na geração do vídeo {task_id}")
                
            self.logger.debug(f"Vídeo {task_id} em processamento (status {status}). Aguardando 15s...")
            await asyncio.sleep(15)

    @with_retry(max_attempts=3)
    async def export_video(self, task_id: str) -> str:
        """Exporta o vídeo em alta qualidade (se preview=true foi usado)"""
        if not self.api_key:
            return "https://mock.url/final_video_hd.mp4"

        url = f"{self.base_url}/m2v/export"
        data = {
            "taskId": task_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self._get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erro Topview Export ({response.status}): {error_text}")
                
                result = await response.json()
                if result.get("code") != 200:
                    raise Exception(f"Erro na API Topview Export: {result}")
                    
                return result.get("data", {}).get("videoUrl")
