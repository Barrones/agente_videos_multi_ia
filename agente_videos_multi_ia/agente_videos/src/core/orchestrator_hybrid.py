"""
Orquestrador Híbrido - Suporta Modo Automático (Tendências) e Manual (Sheets)
"""

import asyncio
import os
from loguru import logger
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from src.llm.factory import LLMFactory
from src.integrations.elevenlabs_client import ElevenLabsIntegration
from src.integrations.topview_client import TopviewIntegration
from src.integrations.heygen_client import HeyGenIntegration
from src.integrations.discord_client import DiscordIntegration
from src.utils.video_processor import VideoProcessor
from src.research.trend_analyzer import TrendAnalyzer
from src.core.script_generator import ScriptGenerator
from src.utils.retry import with_retry
from src.utils.cache import CacheManager


class OperationMode(Enum):
    """Modos de operação do orquestrador"""
    AUTO = "auto"          # Pesquisa tendências automaticamente
    MANUAL = "manual"      # Lê tarefas do Google Sheets
    HYBRID = "hybrid"      # Ambos em paralelo


class VideoAgentOrchestratorHybrid:
    """Orquestrador híbrido que suporta múltiplos modos de operação"""
    
    def __init__(self, config: Dict[str, Any], mode: str = "hybrid"):
        """
        Inicializa o orquestrador
        
        Args:
            config: Configuração do agente
            mode: Modo de operação ("auto", "manual", "hybrid")
        """
        self.config = config
        self.mode = OperationMode(mode.lower())
        self.is_running = False
        self.interval_seconds = config.get("execution", {}).get("interval_minutes", 60) * 60
        
        # Inicializar LLM
        llm_provider = config.get("llm", {}).get("provider", "gpt")
        llm_config = config.get("llm", {}).get("providers", {}).get(llm_provider, {})
        self.llm = LLMFactory.create(llm_provider, llm_config)
        
        # Inicializar integrações
        self.elevenlabs = ElevenLabsIntegration(config)
        self.topview = TopviewIntegration(config)
        self.heygen = HeyGenIntegration(config)
        self.discord = DiscordIntegration(config)
        self.video_processor = VideoProcessor()
        
        # Inicializar analisadores
        self.trend_analyzer = TrendAnalyzer(llm=self.llm)
        self.script_generator = ScriptGenerator(llm=self.llm)
        
        # Cache
        self.cache = CacheManager(config)
        
        # Diretórios temporários
        os.makedirs("temp_audio", exist_ok=True)
        os.makedirs("temp_video", exist_ok=True)
        
        logger.info(f"✅ Orquestrador Híbrido inicializado em modo: {self.mode.value}")

    # ────────────────────────────────────────────────────────────────────────
    # MÉTODOS PÚBLICOS
    # ────────────────────────────────────────────────────────────────────────

    async def start_daemon(self):
        """Inicia o loop contínuo do agente"""
        self.is_running = True
        logger.info(f"🚀 Iniciando daemon em modo {self.mode.value}...")
        
        try:
            while self.is_running:
                await self.run_cycle()
                logger.info(f"⏳ Ciclo concluído. Aguardando {self.interval_seconds/60} minutos...")
                await asyncio.sleep(self.interval_seconds)
        except Exception as e:
            logger.error(f"❌ Erro crítico no daemon: {e}")
            raise

    def stop(self):
        """Para o loop contínuo"""
        self.is_running = False
        logger.info("🛑 Sinal de parada recebido.")

    async def run_cycle(self):
        """Executa um ciclo completo de geração de vídeos"""
        logger.info(f"▶️ Iniciando ciclo em modo {self.mode.value}...")
        
        tasks_to_process = []
        
        # Modo automático: pesquisar tendências
        if self.mode in [OperationMode.AUTO, OperationMode.HYBRID]:
            logger.info("🔍 Modo automático: pesquisando tendências...")
            auto_tasks = await self._get_auto_tasks()
            tasks_to_process.extend(auto_tasks)
        
        # Modo manual: ler do Google Sheets
        if self.mode in [OperationMode.MANUAL, OperationMode.HYBRID]:
            logger.info("📋 Modo manual: lendo tarefas do Google Sheets...")
            manual_tasks = await self._get_manual_tasks()
            tasks_to_process.extend(manual_tasks)
        
        if not tasks_to_process:
            logger.info("ℹ️ Nenhuma tarefa encontrada para processar.")
            return
        
        logger.info(f"📊 Encontradas {len(tasks_to_process)} tarefas. Iniciando processamento paralelo...")
        
        # Processar tarefas em paralelo
        max_workers = self.config.get("execution", {}).get("max_parallel_tasks", 3)
        semaphore = asyncio.Semaphore(max_workers)
        
        tasks = [self.process_single_task(task, semaphore) for task in tasks_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Contar sucessos
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        logger.info(f"✅ Ciclo finalizado. Sucesso: {success_count}/{len(tasks_to_process)}")

    async def process_single_task(self, task: Dict[str, Any], semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Processa a geração de um único vídeo de ponta a ponta"""
        async with semaphore:
            task_id = task.get("id", f"task_{datetime.now().timestamp()}")
            pais = task.get("pais", "Brasil")
            vertical = task.get("vertical", "Geral")
            
            logger.info(f"🎬 [{task_id}] Iniciando processamento: {pais} - {vertical}")
            
            try:
                # 1. Pesquisar Tendências
                logger.info(f"[{task_id}] 🔍 Pesquisando tendências...")
                trend_data = await self.trend_analyzer.analyze_trends(
                    country=pais,
                    vertical=vertical,
                    language=task.get("idioma", "Português")
                )
                
                # 2. Gerar Roteiro
                logger.info(f"[{task_id}] ✍️ Gerando roteiro...")
                script_data = await self.script_generator.generate_script(
                    country=pais,
                    vertical=vertical,
                    language=task.get("idioma", "Português"),
                    trend_data=trend_data,
                    extra_prompt=task.get("prompt_extra", "")
                )
                
                # 3. Gerar Áudio
                logger.info(f"[{task_id}] 🎵 Gerando áudio...")
                audio_path = await self._generate_audio(task_id, script_data)
                
                # 4. Gerar Vídeo (Topview com fallback HeyGen)
                logger.info(f"[{task_id}] 🎥 Gerando vídeo...")
                video_url = await self._generate_video(task_id, task, script_data, vertical)
                
                # 5. Pós-processamento
                logger.info(f"[{task_id}] 🎨 Aplicando efeitos UGC...")
                final_video_url = await self._post_process_video(task_id, video_url)
                
                # 6. Enviar para Aprovação
                logger.info(f"[{task_id}] 📤 Enviando para aprovação no Discord...")
                msg_id = await self.discord.send_approval_message(task, final_video_url, script_data)
                
                # 7. Aguardar Aprovação
                logger.info(f"[{task_id}] ⏳ Aguardando aprovação humana...")
                is_approved = await self.discord.wait_for_approval(msg_id)
                
                if is_approved:
                    logger.info(f"[{task_id}] ✅ Vídeo APROVADO!")
                    # TODO: Salvar no Google Drive
                    return {"success": True, "task_id": task_id, "video_url": final_video_url}
                else:
                    logger.info(f"[{task_id}] ❌ Vídeo REJEITADO.")
                    return {"success": False, "task_id": task_id, "reason": "rejected"}
                
            except Exception as e:
                logger.error(f"[{task_id}] ❌ Falha no processamento: {e}")
                return {"success": False, "task_id": task_id, "error": str(e)}

    # ────────────────────────────────────────────────────────────────────────
    # MÉTODOS PRIVADOS - OBTENÇÃO DE TAREFAS
    # ────────────────────────────────────────────────────────────────────────

    async def _get_auto_tasks(self) -> List[Dict[str, Any]]:
        """Gera tarefas automaticamente baseado em tendências"""
        try:
            # Pesquisar tendências principais
            trends = await self.trend_analyzer.analyze_trends(
                country="Brasil",
                vertical="Geral",
                language="Português"
            )
            
            # Criar tarefa baseada na tendência
            task = {
                "id": f"auto_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "pais": "Brasil",
                "vertical": trends.get("vertical", "Geral"),
                "idioma": "Português",
                "prompt_extra": f"Focar em: {trends.get('trending_topic', 'tendência atual')}",
                "source": "auto"
            }
            
            return [task]
        
        except Exception as e:
            logger.error(f"❌ Erro ao obter tarefas automáticas: {e}")
            return []

    async def _get_manual_tasks(self) -> List[Dict[str, Any]]:
        """Lê tarefas do Google Sheets"""
        try:
            # TODO: Integrar com Google Sheets
            # Por enquanto, retornar lista vazia
            logger.info("📋 Lendo tarefas do Google Sheets...")
            # tasks = await self.sheets_client.get_pending_tasks()
            # return tasks
            return []
        
        except Exception as e:
            logger.error(f"❌ Erro ao obter tarefas do Sheets: {e}")
            return []

    # ────────────────────────────────────────────────────────────────────────
    # MÉTODOS PRIVADOS - PROCESSAMENTO
    # ────────────────────────────────────────────────────────────────────────

    @with_retry(max_attempts=3, min_wait=2, max_wait=10)
    async def _generate_audio(self, task_id: str, script_data: Dict[str, Any]) -> str:
        """Gera áudio do script"""
        audio_path = f"temp_audio/{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        voice_id = self.config.get("apis", {}).get("elevenlabs", {}).get("default_voice_id", "mock_voice")
        
        await self.elevenlabs.generate_audio(
            script_data.get("script_text", ""),
            voice_id,
            audio_path
        )
        
        return audio_path

    @with_retry(max_attempts=3, min_wait=2, max_wait=10)
    async def _generate_video(
        self,
        task_id: str,
        task: Dict[str, Any],
        script_data: Dict[str, Any],
        vertical: str
    ) -> str:
        """Gera vídeo com Topview (fallback HeyGen)"""
        
        # Selecionar avatar e voz baseado na vertical
        avatar_id, voice_id = self._select_avatar_voice(vertical)
        
        try:
            # Tentar Topview primeiro
            logger.info(f"[{task_id}] Tentando Topview...")
            
            topview_task_id = await self.topview.submit_task(
                script=script_data.get("script_text", ""),
                avatar_id=avatar_id,
                voice_id=voice_id,
                image_url=task.get("product_link", "https://www.amazon.com/dp/B0CXVSRY56"),
                language=script_data.get("topview_lang", "en")
            )
            
            task_result = await self.topview.wait_for_completion(topview_task_id)
            video_url = task_result.get("videoUrl") or task_result.get("previewVideoUrl")
            
            if video_url:
                logger.info(f"[{task_id}] ✅ Vídeo gerado com Topview")
                return video_url
            
        except Exception as e:
            logger.warning(f"[{task_id}] ⚠️ Topview falhou: {e}. Tentando HeyGen...")
        
        # Fallback para HeyGen
        try:
            logger.info(f"[{task_id}] Tentando HeyGen...")
            
            video_id = await self.heygen.generate_video(
                avatar_id="default_ugc_avatar",
                audio_url="https://mock.url/audio.mp3"
            )
            
            video_url = await self.heygen.wait_for_completion(video_id)
            logger.info(f"[{task_id}] ✅ Vídeo gerado com HeyGen")
            return video_url
        
        except Exception as e:
            logger.error(f"[{task_id}] ❌ HeyGen também falhou: {e}")
            raise

    @with_retry(max_attempts=2, min_wait=1, max_wait=5)
    async def _post_process_video(self, task_id: str, video_url: str) -> str:
        """Aplica efeitos UGC ao vídeo"""
        # TODO: Implementar pós-processamento com FFmpeg
        logger.info(f"[{task_id}] Pós-processamento: usando vídeo original")
        return video_url

    def _select_avatar_voice(self, vertical: str) -> tuple:
        """Seleciona avatar e voz baseado na vertical"""
        
        if "Finanç" in vertical or "Finance" in vertical or "Cartão" in vertical:
            return ("avatar_professional_01", "voice_professional_trust")
        
        elif "Shein" in vertical or "Produto" in vertical or "Moda" in vertical:
            return ("avatar_influencer_02", "voice_casual_excited")
        
        elif "Saúde" in vertical or "Beleza" in vertical:
            return ("avatar_wellness_01", "voice_calm_friendly")
        
        else:
            return ("avatar_default", None)

    # ────────────────────────────────────────────────────────────────────────
    # MÉTODOS AUXILIARES
    # ────────────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do orquestrador"""
        return {
            "is_running": self.is_running,
            "mode": self.mode.value,
            "interval_seconds": self.interval_seconds,
            "timestamp": datetime.now().isoformat()
        }
