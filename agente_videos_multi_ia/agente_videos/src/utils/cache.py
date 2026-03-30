import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger

class CacheManager:
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("cache", {}).get("enabled", True)
        self.cache_file = config.get("cache", {}).get("file_path", "logs/cache.json")
        self.ttl_hours = config.get("cache", {}).get("ttl_hours", 24)
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if not self.enabled or not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {str(e)}")
            return {}

    def _save_cache(self):
        if not self.enabled:
            return
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {str(e)}")

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
            
        entry = self.cache_data.get(key)
        if not entry:
            return None
            
        timestamp = datetime.fromisoformat(entry["timestamp"])
        if datetime.now() - timestamp > timedelta(hours=self.ttl_hours):
            del self.cache_data[key]
            self._save_cache()
            return None
            
        return entry["data"]

    def set(self, key: str, data: Any):
        if not self.enabled:
            return
            
        self.cache_data[key] = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self._save_cache()

    def generate_key(self, task: Dict[str, Any]) -> str:
        """Gera uma chave única baseada nos dados da tarefa"""
        return f"{task.get('pais')}_{task.get('vertical')}_{datetime.now().strftime('%Y%m%d')}"
