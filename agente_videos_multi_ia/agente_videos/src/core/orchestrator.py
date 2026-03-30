import asyncio
import os
from loguru import logger
from typing import Dict, Any, List
from datetime import datetime

from src.llm.factory import LLMFactory
from src.integrations.elevenlabs_client import ElevenLabsIntegration
from src.integrations.heygen_client import HeyGenIntegration
from src.integrations.discord_client import DiscordIntegration
from src.utils.video_processor import VideoProcessor

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
        self.heygen = HeyGenIntegration(config)
        self.discord = DiscordIntegration(config)
        self.video_processor = VideoProcessor()
        
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
                # 1. Gerar Roteiro (LLM Dinâmico)
                logger.info(f"[{pais}] Gerando roteiro com {self.llm.__class__.__name__}...")
                
                # Adaptando a chamada para a nova interface base_llm
                prompt = f"Crie um roteiro de vídeo UGC para {vertical} no país {pais}. Idioma: {task.get('idioma')}. Foco: {task.get('prompt_base')}"
                system_prompt = "Você é um especialista em marketing digital criando roteiros de alta conversão no estilo UGC (User Generated Content)."
                
                roteiro_texto = await self.llm.generate_script(prompt, system_prompt)
                
                # Simulando a estrutura de dados esperada pelo resto do código
                script_data = {
                    "roteiro_completo": roteiro_texto,
                    "gancho": "Gancho gerado",
                    "corpo": "Corpo gerado",
                    "cta": "CTA gerado"
                }
                
                # 2. Gerar Áudio (ElevenLabs)
                logger.info(f"[{pais}] Gerando áudio...")
                audio_path = f"temp_audio/{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
                voice_id = self.config.get("apis", {}).get("elevenlabs", {}).get("default_voice_id", "mock_voice")
                await self.elevenlabs.generate_audio(script_data["roteiro_completo"], voice_id, audio_path)
                
                # Nota: Em um cenário real, precisaríamos fazer upload do áudio para uma URL pública (S3)
                # Aqui usaremos uma URL mockada para a API do Topview
                audio_url = "https://mock.url/audio.mp3" 
                
                # 3. Gerar Vídeo UGC (HeyGen)
                logger.info(f"[{pais}] Submetendo vídeo para HeyGen (UGC Style)...")
                heygen_video_id = await self.heygen.generate_video(
                    avatar_id=task.get("avatar_id", "default_ugc_avatar"),
                    audio_url=audio_url,
                    background_url=task.get("background_url")
                )
                
                logger.info(f"[{pais}] Aguardando processamento do vídeo...")
                raw_video_url = await self.heygen.wait_for_completion(heygen_video_id)
                
                # 4. Pós-processamento (Efeito Celular/UGC)
                logger.info(f"[{pais}] Aplicando filtros UGC (FFmpeg)...")
                # Em um cenário real, faríamos o download do raw_video_url primeiro
                # Aqui simulamos o processamento
                processed_video_path = f"temp_video/{task_id}_ugc.mp4"
                # await self.video_processor.apply_ugc_filter("downloaded_raw.mp4", processed_video_path)
                final_preview_url = raw_video_url # Usando a URL gerada para preview
                
                # 5. Enviar para Aprovação (Discord)
                logger.info(f"[{pais}] Enviando para aprovação no Discord...")
                msg_id = await self.discord.send_approval_message(task, final_preview_url, script_data)
                
                # 6. Aguardar Aprovação
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
