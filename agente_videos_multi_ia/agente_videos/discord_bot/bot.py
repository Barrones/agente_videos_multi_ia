"""
Bot Discord Unificado — Agente UGC
Pipeline: Pesquisa de Tendências + Geração de Vídeos + Aprovação Humana
"""

import discord
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# Importar módulos do agente unificado
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.trend_analyzer import TrendAnalyzer
from src.core.script_generator import ScriptGenerator
from src.integrations.elevenlabs_client import ElevenLabsIntegration
from src.integrations.topview_client import TopviewIntegration
from src.integrations.heygen_client import HeyGenIntegration
from src.llm.factory import LLMFactory
from src.utils.config import load_config

# Carregar variáveis de ambiente
load_dotenv()

# Configuração
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")

# Logger
logger.add("logs/bot_{time}.log", rotation="10 MB", retention="7 days", level="INFO")

# Carregar configuração
config = load_config("config/settings.yaml")

# Inicializar integrações
llm_provider = config.get("llm", {}).get("provider", "gemini")
llm_config = config.get("llm", {}).get("providers", {}).get(llm_provider, {})
llm = LLMFactory.create(llm_provider, llm_config)

trend_analyzer = TrendAnalyzer(llm=llm)
script_generator = ScriptGenerator(llm=llm)
elevenlabs = ElevenLabsIntegration(config)
topview = TopviewIntegration(config)
heygen = HeyGenIntegration(config)

# Estado do bot
bot_state = {
    "tarefas_em_processamento": {},
    "reacoes_mapa": {}  # {message_id: {"tarefa_id": str, "dados": dict}}
}

# Intents do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)


# ────────────────────────────────────────────────────────────────────────────
# EVENTOS DO BOT
# ────────────────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    """Evento disparado quando o bot conecta ao Discord"""
    logger.info(f"✅ Bot conectado como {client.user}")
    logger.info(f"📍 Aguardando comandos no canal {CHANNEL_ID}")


@client.event
async def on_message(message):
    """Evento disparado quando uma mensagem é recebida"""
    
    # Ignorar mensagens do próprio bot
    if message.author == client.user:
        return
    
    # Ignorar mensagens em canais diferentes
    if message.channel.id != CHANNEL_ID:
        return
    
    # Processar comandos
    if message.content.startswith("/gerar_video"):
        await handle_gerar_video(message)
    
    elif message.content.startswith("/status"):
        await handle_status(message)
    
    elif message.content.startswith("/tendencias"):
        await handle_tendencias(message)


@client.event
async def on_reaction_add(reaction, user):
    """Evento disparado quando uma reação é adicionada"""
    
    # Ignorar reações do próprio bot
    if user == client.user:
        return
    
    message_id = reaction.message.id
    
    # Verificar se é uma reação de aprovação/rejeição
    if message_id in bot_state["reacoes_mapa"]:
        tarefa = bot_state["reacoes_mapa"][message_id]
        
        if reaction.emoji == "✅":
            logger.info(f"✅ Tarefa {tarefa['tarefa_id']} APROVADA por {user.name}")
            await reaction.message.reply(f"✅ Vídeo aprovado! Salvando no Google Drive...")
            # TODO: Salvar no Google Drive
        
        elif reaction.emoji == "❌":
            logger.info(f"❌ Tarefa {tarefa['tarefa_id']} REJEITADA por {user.name}")
            await reaction.message.reply(f"❌ Vídeo rejeitado. Motivo: {tarefa.get('motivo', 'Não especificado')}")


# ────────────────────────────────────────────────────────────────────────────
# HANDLERS DE COMANDOS
# ────────────────────────────────────────────────────────────────────────────

async def handle_gerar_video(message):
    """Manipulador do comando /gerar_video"""
    
    try:
        # Extrair parâmetros
        # Formato: /gerar_video pais=Brasil vertical=Finanças idioma=Português
        params = {}
        partes = message.content.split()
        
        for parte in partes[1:]:
            if "=" in parte:
                chave, valor = parte.split("=", 1)
                params[chave.lower()] = valor
        
        pais = params.get("pais", "Brasil")
        vertical = params.get("vertical", "Finanças")
        idioma = params.get("idioma", "Português")
        
        # Enviar confirmação
        embed = discord.Embed(
            title="🎬 Gerando Vídeo",
            description=f"País: {pais}\nVertical: {vertical}\nIdioma: {idioma}",
            color=discord.Color.blue()
        )
        msg = await message.reply(embed=embed)
        
        # Pesquisar tendências
        logger.info(f"🔍 Pesquisando tendências para {vertical} em {pais}...")
        trend_data = await trend_analyzer.analyze_trends(
            country=pais,
            vertical=vertical,
            language=idioma
        )
        
        # Gerar roteiro
        logger.info(f"✍️ Gerando roteiro...")
        script_data = await script_generator.generate_script(
            country=pais,
            vertical=vertical,
            language=idioma,
            trend_data=trend_data
        )
        
        # Gerar áudio
        logger.info(f"🎵 Gerando áudio...")
        audio_path = f"temp_audio/discord_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        voice_id = config.get("apis", {}).get("elevenlabs", {}).get("default_voice_id", "mock_voice")
        await elevenlabs.generate_audio(script_data.get("script_text", ""), voice_id, audio_path)
        
        # Gerar vídeo (tentar Topview primeiro, depois HeyGen)
        logger.info(f"🎥 Gerando vídeo com Topview...")
        try:
            topview_task_id = await topview.submit_task(
                script=script_data.get("script_text", ""),
                avatar_id="avatar_professional_01",
                voice_id=None,
                image_url="https://www.amazon.com/dp/B0CXVSRY56",
                language=script_data.get("topview_lang", "en")
            )
            
            # Aguardar conclusão
            task_result = await topview.wait_for_completion(topview_task_id)
            video_url = task_result.get("videoUrl") or task_result.get("previewVideoUrl", "https://mock.url/video.mp4")
            
        except Exception as e:
            logger.warning(f"⚠️ Topview falhou, tentando HeyGen: {e}")
            video_id = await heygen.generate_video(
                avatar_id="default_ugc_avatar",
                audio_url="https://mock.url/audio.mp3"
            )
            video_url = await heygen.wait_for_completion(video_id)
        
        # Enviar para aprovação
        embed_resultado = discord.Embed(
            title="✅ Vídeo Gerado!",
            description=f"Tendência: {trend_data.get('trending_topic', 'N/A')}\nURL: {video_url}",
            color=discord.Color.green()
        )
        embed_resultado.add_field(
            name="Roteiro",
            value=script_data.get("script_text", "N/A")[:500],
            inline=False
        )
        
        resultado_msg = await message.reply(embed=embed_resultado)
        
        # Adicionar reações para aprovação
        await resultado_msg.add_reaction("✅")
        await resultado_msg.add_reaction("❌")
        
        # Registrar para rastreamento de reações
        bot_state["reacoes_mapa"][resultado_msg.id] = {
            "tarefa_id": f"discord_{datetime.now().timestamp()}",
            "pais": pais,
            "vertical": vertical,
            "idioma": idioma,
            "video_url": video_url,
            "script": script_data.get("script_text", "")
        }
        
        logger.info(f"✅ Vídeo gerado e enviado para aprovação")
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar vídeo: {e}")
        await message.reply(f"❌ Erro ao gerar vídeo: {str(e)[:200]}")


async def handle_status(message):
    """Manipulador do comando /status"""
    
    try:
        tarefas_processando = len(bot_state["tarefas_em_processamento"])
        
        embed = discord.Embed(
            title="📊 Status do Agente",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="✅ Online", inline=True)
        embed.add_field(name="Tarefas em Processamento", value=str(tarefas_processando), inline=True)
        embed.add_field(name="Modo", value="Híbrido (Tendências + Manual)", inline=True)
        embed.set_footer(text=f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")
        
        await message.reply(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        await message.reply(f"❌ Erro ao obter status: {str(e)}")


async def handle_tendencias(message):
    """Manipulador do comando /tendencias"""
    
    try:
        # Extrair país
        partes = message.content.split()
        pais = partes[1] if len(partes) > 1 else "Brasil"
        
        logger.info(f"🔍 Pesquisando tendências para {pais}...")
        
        trend_data = await trend_analyzer.analyze_trends(
            country=pais,
            vertical="Geral",
            language="Português"
        )
        
        embed = discord.Embed(
            title=f"🔥 Tendências em Alta - {pais}",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Tópico Principal",
            value=trend_data.get("trending_topic", "N/A"),
            inline=False
        )
        embed.add_field(
            name="Crescimento de Buscas",
            value=trend_data.get("search_volume_growth", "N/A"),
            inline=True
        )
        embed.add_field(
            name="Público Alvo",
            value=trend_data.get("target_audience", "N/A"),
            inline=True
        )
        
        dores = ", ".join(trend_data.get("pain_points", []))
        embed.add_field(name="Dores do Público", value=dores or "N/A", inline=False)
        
        ganchos = ", ".join(trend_data.get("viral_hooks", []))
        embed.add_field(name="Ganchos Virais", value=ganchos or "N/A", inline=False)
        
        embed.add_field(
            name="Contexto Cultural",
            value=trend_data.get("cultural_context", "N/A"),
            inline=False
        )
        
        await message.reply(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Erro ao pesquisar tendências: {e}")
        await message.reply(f"❌ Erro ao pesquisar tendências: {str(e)[:200]}")


# ────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO
# ────────────────────────────────────────────────────────────────────────────

async def main():
    """Função principal para iniciar o bot"""
    
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_BOT_TOKEN não configurado!")
        return
    
    logger.info("🚀 Iniciando Bot Discord...")
    
    async with client:
        await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
