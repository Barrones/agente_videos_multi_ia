from abc import ABC
from typing import Dict, Any
from loguru import logger

class BaseIntegration(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger.bind(integration=self.__class__.__name__)
        self._setup()

    def _setup(self):
        """Método para inicialização específica de cada integração"""
        pass
