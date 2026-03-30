import asyncio
import os
from loguru import logger
from typing import Dict, Any, List
from datetime import datetime

from src.llm.factory import LLMFactory
from src.integrations.elevenlabs_client import ElevenLabsIntegration
from src.integrations.topview_client import TopviewIntegration
from src.integrations.discord_client import DiscordIntegration
from src.utils.video_processor import VideoProcessor
from src.research.trend_analyzer import TrendAnalyzer
from src.core.script_generator import ScriptGenerator

class VideoAgentOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.interval_seconds = config.get("execution", {}).get("interval_minutes", 60) * 60
        
        # Inicializar integrações
        llm_provider = config.get("llm", {}).get("provider", "gpt")
        llm_config = config.get("llm", {}).get("providers", {}).get(llm_provider, {})
        self.llm = LLMFactory.create(llm_provider, llm_config)
        
        self.elevenlabs = ElevenLabsIntegration(config)
        self.topview = TopviewIntegration(config)
        self.discord = DiscordIntegration(config)
        self.video_processor = VideoProcessor()
        self.trend_analyzer = TrendAnalyzer(llm=self.llm)
        self.script_generator = ScriptGenerator(llm=self.llm)
        
        # Diretórios temporários
        os.makedirs("temp_audio", exist_ok=True)
        os.makedirs("temp_video", exist_ok=True)

    async def start_daemon(self):
        """Inicia o loop contínuo do agente"""
        self.is_running = True
        while self.is_running:
            try:
                await self.run_cycle()
                logger.info(f"Ciclo concluído. Aguardando {self.interval_seconds/60} minutos...")
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                logger.error(f"Erro crítico no ciclo principal: {str(e)}")
                await asyncio.sleep(60)

    def stop(self):
        """Para o loop contínuo"""
        self.is_running = False
        logger.info("Sinal de parada recebido.")

    async def run_cycle(self):
        """Executa um ciclo completo de geração de vídeos"""
        logger.info("Iniciando novo ciclo de processamento...")
        
        # Mock de tarefas (na próxima fase integraremos com Google Sheets)
        active_tasks = [
            {
                "id": "task_1",
                "pais": "Brasil", 
                "vertical": "Finanças - Cartão", 
                "idioma": "Português",
                "prompt_base": "Focar em pessoas com nome sujo e score baixo",
                "avatar_id": "avatar_masculino_1"
            }
        ]
        
        if not active_tasks:
            logger.info("Nenhuma tarefa ativa encontrada na planilha.")
            return

        logger.info(f"Encontradas {len(active_tasks)} tarefas ativas. Iniciando processamento paralelo...")

        max_workers = self.config.get("execution", {}).get("max_parallel_tasks", 3)
        semaphore = asyncio.Semaphore(max_workers)
        
        tasks = [self.process_single_task(task, semaphore) for task in active_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        logger.info(f"Ciclo finalizado. Sucesso: {success_count}/{len(active_tasks)}")

    async def process_single_task(self, task: Dict[str, Any], semaphore: asyncio.Semaphore) -> bool:
        """Processa a geração de um único vídeo de ponta a ponta"""
        async with semaphore:
            pais = task.get("pais")
            vertical = task.get("vertical")
            task_id = task.get("id")
            logger.info(f"[{pais} - {vertical}] Iniciando processamento...")
            
            try:
                # 1. Pesquisar Tendências
                logger.info(f"[{pais}] Pesquisando tendências para {vertical}...")
                trend_data = await self.trend_analyzer.analyze_trends(
                    country=pais,
                    vertical=vertical,
                    language=task.get("idioma", "Português")
                )
                
                # 2. Gerar Roteiro Contextualizado
                logger.info(f"[{pais}] Gerando roteiro baseado na tendência: {trend_data.get('trending_topic')}...")
                script_data = await self.script_generator.generate_script(
                    country=pais,
                    vertical=vertical,
                    language=task.get("idioma", "Português"),
                    trend_data=trend_data
                )
                
                # Adaptando para a estrutura esperada pelo resto do código
                script_data["roteiro_completo"] = script_data.get("script_text", "")
                
                # 3. Gerar Áudio (ElevenLabs)
                logger.info(f"[{pais}] Gerando áudio...")
                audio_path = f"temp_audio/{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
                voice_id = self.config.get("apis", {}).get("elevenlabs", {}).get("default_voice_id", "mock_voice")
                await self.elevenlabs.generate_audio(script_data["roteiro_completo"], voice_id, audio_path)
                
                # Nota: Em um cenário real, precisaríamos fazer upload do áudio para uma URL pública (S3)
                # Aqui usaremos uma URL mockada para a API do Topview
                audio_url = "https://mock.url/audio.mp3" 
                
                # 4. Gerar Vídeo UGC (Topview)
                logger.info(f"[{pais}] Submetendo vídeo para Topview (Avatar Marketing Video)...")
                
                # Otimização de avatar e voz baseada na vertical
                # Finance: tom profissional, Shein: estilo influencer
                if "Finanç" in vertical or "Finance" in vertical:
                    topview_avatar_id = "avatar_professional_01" # Exemplo de ID para avatar profissional
                    topview_voice_id = "voice_professional_trust"
                elif "Shein" in vertical or "Produto" in vertical:
                    topview_avatar_id = "avatar_influencer_02" # Exemplo de ID para avatar influencer
                    topview_voice_id = "voice_casual_excited"
                else:
                    topview_avatar_id = task.get("avatar_id")
                    topview_voice_id = None
                
                # Para Avatar Marketing Video, precisamos passar o script e opcionalmente um link de produto
                # Vamos usar um link genérico se não houver um específico
                product_link = task.get("product_link", "https://www.amazon.com/dp/B0CXVSRY56")
                
                topview_task_id = await self.topview.submit_task(
                    script=script_data["roteiro_completo"],
                    avatar_id=topview_avatar_id,
                    voice_id=topview_voice_id,
                    image_url=product_link,
                    language=script_data.get("topview_lang", "en")
                )
                
                logger.info(f"[{pais}] Aguardando processamento do vídeo (Task ID: {topview_task_id})...")
                task_result = await self.topview.wait_for_completion(topview_task_id)
                
                # A API retorna videoUrl ou previewVideoUrl dependendo se preview=true ou false
                raw_video_url = task_result.get("videoUrl") or task_result.get("previewVideoUrl", "https://mock.url/preview.mp4")
                
                # 5. Pós-processamento (Efeito Celular/UGC)
                logger.info(f"[{pais}] Aplicando filtros UGC (FFmpeg)...")
                # Em um cenário real, faríamos o download do raw_video_url primeiro
                # Aqui simulamos o processamento
                processed_video_path = f"temp_video/{task_id}_ugc.mp4"
                # await self.video_processor.apply_ugc_filter("downloaded_raw.mp4", processed_video_path)
                final_preview_url = raw_video_url # Usando a URL gerada para preview
                
                # 6. Enviar para Aprovação (Discord)
                logger.info(f"[{pais}] Enviando para aprovação no Discord...")
                msg_id = await self.discord.send_approval_message(task, final_preview_url, script_data)
                
                # 7. Aguardar Aprovação
                logger.info(f"[{pais}] Aguardando aprovação humana...")
                is_approved = await self.discord.wait_for_approval(msg_id)
                
                if is_approved:
                    logger.info(f"[{pais}] Vídeo APROVADO! Salvando versão final UGC...")
                    # Na próxima fase: Salvar no Google Drive e registrar no Sheets
                    return True
                else:
                    logger.info(f"[{pais}] Vídeo REJEITADO.")
                    return False
                
            except Exception as e:
                logger.error(f"[{pais} - {vertical}] Falha no processamento: {str(e)}")
                return False
