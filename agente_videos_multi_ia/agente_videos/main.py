import asyncio
import argparse
from loguru import logger
from src.core.orchestrator import VideoAgentOrchestrator
from src.utils.config import load_config
from src.api.server import start_server

async def main():
    parser = argparse.ArgumentParser(description="Agente de Vídeos de Alta Conversão")
    parser.add_argument("--config", type=str, default="config/settings.yaml", help="Caminho para o arquivo de configuração")
    parser.add_argument("--run-once", action="store_true", help="Executa apenas uma vez e encerra")
    args = parser.parse_args()

    logger.add("logs/agente_{time}.log", rotation="10 MB", retention="7 days", level="INFO")
    logger.info("🚀 Iniciando Agente de Vídeos de Alta Conversão...")

    config = load_config(args.config)
    orchestrator = VideoAgentOrchestrator(config)

    # Iniciar Dashboard
    start_server(port=8000)

    if args.run_once:
        logger.info("Executando em modo único (run-once)")
        await orchestrator.run_cycle()
    else:
        logger.info("Executando em modo contínuo")
        await orchestrator.start_daemon()

if __name__ == "__main__":
    asyncio.run(main())
