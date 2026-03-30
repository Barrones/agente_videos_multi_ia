from typing import Dict, Any
from loguru import logger
from .base_llm import BaseLLM
from .providers.gpt_provider import GPTProvider
from .providers.claude_provider import ClaudeProvider
from .providers.gemini_provider import GeminiProvider

class LLMFactory:
    """Factory para criar instâncias de LLM dinamicamente"""
    
    @staticmethod
    def create(provider_name: str, config: Dict[str, Any]) -> BaseLLM:
        """
        Cria e retorna uma instância do provedor LLM solicitado.
        
        Args:
            provider_name: Nome do provedor (gpt, claude, gemini, manus, copilot)
            config: Dicionário com as configurações (api_key, model, etc)
        """
        provider_name = provider_name.lower()
        logger.info(f"Inicializando LLM Provider: {provider_name}")
        
        if provider_name == "gpt" or provider_name == "openai":
            return GPTProvider(config)
            
        elif provider_name == "claude" or provider_name == "anthropic":
            return ClaudeProvider(config)
            
        elif provider_name == "gemini" or provider_name == "google":
            return GeminiProvider(config)
            
        elif provider_name == "manus":
            # Manus usa a mesma API compatível com OpenAI
            config["base_url"] = "https://api.manus.im/v1/chat/completions" # Exemplo
            return GPTProvider(config)
            
        elif provider_name == "copilot":
            # Copilot via API (exemplo de implementação futura)
            logger.warning("Copilot provider ainda não implementado nativamente. Usando GPT como fallback.")
            return GPTProvider(config)
            
        else:
            logger.error(f"Provedor LLM desconhecido: {provider_name}. Usando GPT como fallback.")
            return GPTProvider(config)
