from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLM(ABC):
    """Interface base para todos os provedores de LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key")
        self.model = config.get("model")
        self._setup()
        
    @abstractmethod
    def _setup(self):
        """Inicializa o cliente específico da IA"""
        pass
        
    @abstractmethod
    async def generate_script(self, prompt: str, system_prompt: str = None) -> str:
        """Gera o roteiro do vídeo"""
        pass
        
    @abstractmethod
    async def analyze_trend(self, country: str, vertical: str) -> str:
        """Analisa tendências para um país e vertical"""
        pass
