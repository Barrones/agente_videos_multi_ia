import yaml
import os
from pathlib import Path
from typing import Dict, Any
from loguru import logger
from dotenv import load_dotenv

def load_config(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """Carrega a configuração do arquivo YAML e mescla com variáveis de ambiente"""
    # Carregar .env se existir
    load_dotenv()
    
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Arquivo de configuração não encontrado em {config_path}. Usando configuração padrão.")
        return get_default_config()
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Substituir variáveis de ambiente no config (ex: ${OPENAI_API_KEY})
        config = resolve_env_vars(config)
        return config
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {str(e)}")
        return get_default_config()

def resolve_env_vars(config: Any) -> Any:
    """Percorre o dicionário e substitui strings no formato ${VAR_NAME} pelo valor da variável de ambiente"""
    if isinstance(config, dict):
        return {k: resolve_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_env_vars(i) for i in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.environ.get(env_var, config)
    return config

def get_default_config() -> Dict[str, Any]:
    return {
        "execution": {
            "interval_minutes": 60,
            "max_parallel_tasks": 3
        },
        "apis": {
            "openai": {"model": "gpt-4o"},
            "elevenlabs": {"model": "eleven_turbo_v2_5"},
            "topview": {"quality": "1080p"}
        }
    }
