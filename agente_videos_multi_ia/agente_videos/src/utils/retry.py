from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
import aiohttp
import asyncio

def log_retry_attempt(retry_state):
    """Loga a tentativa de retry"""
    logger.warning(f"Tentativa {retry_state.attempt_number} falhou. Retentando em {retry_state.next_action.sleep} segundos...")

def with_retry(max_attempts=3, min_wait=2, max_wait=10):
    """Decorator para retry automático em funções assíncronas"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, Exception)),
        after=log_retry_attempt,
        reraise=True
    )
