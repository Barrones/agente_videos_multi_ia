"""
Suite de Testes de Integração - Agente Unificado
Testa todos os módulos e integrações
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime

# Adicionar caminho do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import load_config
from src.llm.factory import LLMFactory
from src.research.trend_analyzer import TrendAnalyzer
from src.core.script_generator import ScriptGenerator
from src.core.orchestrator_hybrid import VideoAgentOrchestratorHybrid, OperationMode
from src.integrations.elevenlabs_client import ElevenLabsIntegration
from src.integrations.topview_client import TopviewIntegration
from src.integrations.heygen_client import HeyGenIntegration
from src.integrations.discord_client import DiscordIntegration
from src.api.server_unified import (
    dashboard_state, add_tendencia, add_tarefa_ativa, 
    add_video_recente, add_log_atividade
)


# ────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def config():
    """Carrega configuração para testes"""
    return load_config("config/settings.yaml")


@pytest.fixture
def llm(config):
    """Cria instância de LLM para testes"""
    provider = config.get("llm", {}).get("provider", "gpt")
    llm_config = config.get("llm", {}).get("providers", {}).get(provider, {})
    return LLMFactory.create(provider, llm_config)


@pytest.fixture
def orchestrator(config):
    """Cria instância do orquestrador híbrido"""
    return VideoAgentOrchestratorHybrid(config, mode="hybrid")


# ────────────────────────────────────────────────────────────────────────────
# TESTES DE IMPORTS
# ────────────────────────────────────────────────────────────────────────────

class TestImports:
    """Testa se todos os módulos podem ser importados"""
    
    def test_import_config(self):
        """Teste: Importar módulo de configuração"""
        from src.utils.config import load_config
        assert load_config is not None
        print("✅ Config importado")
    
    def test_import_llm_factory(self):
        """Teste: Importar factory de LLM"""
        from src.llm.factory import LLMFactory
        assert LLMFactory is not None
        print("✅ LLMFactory importado")
    
    def test_import_trend_analyzer(self):
        """Teste: Importar analisador de tendências"""
        from src.research.trend_analyzer import TrendAnalyzer
        assert TrendAnalyzer is not None
        print("✅ TrendAnalyzer importado")
    
    def test_import_script_generator(self):
        """Teste: Importar gerador de scripts"""
        from src.core.script_generator import ScriptGenerator
        assert ScriptGenerator is not None
        print("✅ ScriptGenerator importado")
    
    def test_import_orchestrator_hybrid(self):
        """Teste: Importar orquestrador híbrido"""
        from src.core.orchestrator_hybrid import VideoAgentOrchestratorHybrid
        assert VideoAgentOrchestratorHybrid is not None
        print("✅ VideoAgentOrchestratorHybrid importado")
    
    def test_import_integrations(self):
        """Teste: Importar integrações"""
        from src.integrations.topview_client import TopviewIntegration
        from src.integrations.heygen_client import HeyGenIntegration
        from src.integrations.elevenlabs_client import ElevenLabsIntegration
        from src.integrations.discord_client import DiscordIntegration
        
        assert TopviewIntegration is not None
        assert HeyGenIntegration is not None
        assert ElevenLabsIntegration is not None
        assert DiscordIntegration is not None
        print("✅ Todas as integrações importadas")
    
    def test_import_dashboard(self):
        """Teste: Importar dashboard"""
        from src.api.server_unified import app, dashboard_state
        assert app is not None
        assert dashboard_state is not None
        print("✅ Dashboard importado")


# ────────────────────────────────────────────────────────────────────────────
# TESTES DE CONFIGURAÇÃO
# ────────────────────────────────────────────────────────────────────────────

class TestConfiguration:
    """Testa carregamento e validação de configuração"""
    
    def test_load_config(self, config):
        """Teste: Carregar configuração"""
        assert config is not None
        assert "llm" in config
        assert "apis" in config
        print("✅ Configuração carregada")
    
    def test_config_has_required_keys(self, config):
        """Teste: Verificar chaves obrigatórias"""
        required_keys = ["llm", "apis", "execution"]
        for key in required_keys:
            assert key in config, f"Chave obrigatória '{key}' não encontrada"
        print("✅ Todas as chaves obrigatórias presentes")
    
    def test_llm_provider_configured(self, config):
        """Teste: Verificar provedor LLM configurado"""
        provider = config.get("llm", {}).get("provider")
        assert provider is not None
        assert provider in ["gpt", "claude", "gemini", "manus", "copilot"]
        print(f"✅ Provedor LLM configurado: {provider}")


# ────────────────────────────────────────────────────────────────────────────
# TESTES DE LLM
# ────────────────────────────────────────────────────────────────────────────

class TestLLM:
    """Testa inicialização e funcionamento do LLM"""
    
    def test_llm_factory_create(self, config):
        """Teste: Factory cria instância de LLM"""
        provider = config.get("llm", {}).get("provider", "gpt")
        llm_config = config.get("llm", {}).get("providers", {}).get(provider, {})
        
        llm = LLMFactory.create(provider, llm_config)
        assert llm is not None
        print(f"✅ LLM criado: {provider}")
    
    def test_llm_has_required_methods(self, llm):
        """Teste: LLM tem métodos obrigatórios"""
        # Verificar se tem métodos da interface BaseLLM
        assert hasattr(llm, "generate_script"), "LLM deve ter método 'generate_script'"
        assert hasattr(llm, "analyze_trend"), "LLM deve ter método 'analyze_trend'"
        print("✅ LLM tem métodos obrigatórios")


# ────────────────────────────────────────────────────────────────────────────
# TESTES DO ORQUESTRADOR
# ────────────────────────────────────────────────────────────────────────────

class TestOrchestrator:
    """Testa orquestrador híbrido"""
    
    def test_orchestrator_initialization(self, orchestrator):
        """Teste: Inicializar orquestrador"""
        assert orchestrator is not None
        assert orchestrator.mode == OperationMode.HYBRID
        print("✅ Orquestrador inicializado")
    
    def test_orchestrator_modes(self, config):
        """Teste: Testar todos os modos"""
        for mode in ["auto", "manual", "hybrid"]:
            orch = VideoAgentOrchestratorHybrid(config, mode=mode)
            assert orch.mode == OperationMode(mode)
        print("✅ Todos os modos funcionam")
    
    def test_orchestrator_get_status(self, orchestrator):
        """Teste: Obter status do orquestrador"""
        status = orchestrator.get_status()
        assert status is not None
        assert "is_running" in status
        assert "mode" in status
        print("✅ Status do orquestrador obtido")
    
    def test_orchestrator_avatar_selection(self, orchestrator):
        """Teste: Seleção de avatar por vertical"""
        # Finanças
        avatar, voice = orchestrator._select_avatar_voice("Finanças")
        assert avatar == "avatar_professional_01"
        
        # Shein/Produtos
        avatar, voice = orchestrator._select_avatar_voice("Shein")
        assert avatar == "avatar_influencer_02"
        
        # Saúde/Beleza
        avatar, voice = orchestrator._select_avatar_voice("Beleza")
        assert avatar == "avatar_wellness_01"
        
        print("✅ Seleção de avatar funcionando")


# ────────────────────────────────────────────────────────────────────────────
# TESTES DO DASHBOARD
# ────────────────────────────────────────────────────────────────────────────

class TestDashboard:
    """Testa dashboard unificado"""
    
    def test_dashboard_state_structure(self):
        """Teste: Estrutura do estado do dashboard"""
        required_keys = [
            "status", "modo_operacao", "metricas", "tendencias",
            "tarefas_ativas", "topview_tasks", "videos_recentes",
            "atividades_discord", "log_atividades", "stats"
        ]
        
        for key in required_keys:
            assert key in dashboard_state, f"Chave '{key}' não encontrada no dashboard"
        
        print("✅ Estrutura do dashboard válida")
    
    def test_add_tendencia(self):
        """Teste: Adicionar tendência ao dashboard"""
        initial_count = len(dashboard_state["tendencias"])
        
        add_tendencia(
            pais="Brasil",
            vertical="Finanças",
            topico="Cartão de Crédito",
            crescimento="+250%"
        )
        
        assert len(dashboard_state["tendencias"]) == initial_count + 1
        print("✅ Tendência adicionada ao dashboard")
    
    def test_add_tarefa_ativa(self):
        """Teste: Adicionar tarefa ativa"""
        task_id = f"test_task_{datetime.now().timestamp()}"
        
        add_tarefa_ativa(
            task_id=task_id,
            pais="Brasil",
            vertical="Finanças"
        )
        
        assert task_id in dashboard_state["tarefas_ativas"]
        print("✅ Tarefa ativa adicionada")
    
    def test_add_video_recente(self):
        """Teste: Adicionar vídeo recente"""
        initial_count = len(dashboard_state["videos_recentes"])
        
        add_video_recente(
            video_id="test_vid_001",
            pais="Brasil",
            vertical="Finanças",
            status="aprovado",
            url="https://example.com/video.mp4"
        )
        
        assert len(dashboard_state["videos_recentes"]) == initial_count + 1
        print("✅ Vídeo recente adicionado")
    
    def test_add_log_atividade(self):
        """Teste: Adicionar log de atividade"""
        initial_count = len(dashboard_state["log_atividades"])
        
        add_log_atividade(
            nivel="INFO",
            mensagem="Teste de log",
            modulo="test"
        )
        
        assert len(dashboard_state["log_atividades"]) == initial_count + 1
        print("✅ Log de atividade adicionado")


# ────────────────────────────────────────────────────────────────────────────
# TESTES DE INTEGRAÇÃO COMPLETA
# ────────────────────────────────────────────────────────────────────────────

class TestFullIntegration:
    """Testa integração completa de todos os módulos"""
    
    def test_all_modules_work_together(self, config):
        """Teste: Todos os módulos funcionam juntos"""
        try:
            # 1. Carregar config
            assert config is not None
            
            # 2. Criar LLM
            provider = config.get("llm", {}).get("provider", "gpt")
            llm_config = config.get("llm", {}).get("providers", {}).get(provider, {})
            llm = LLMFactory.create(provider, llm_config)
            assert llm is not None
            
            # 3. Criar orquestrador
            orchestrator = VideoAgentOrchestratorHybrid(config, mode="hybrid")
            assert orchestrator is not None
            
            # 4. Verificar integrações
            assert orchestrator.elevenlabs is not None
            assert orchestrator.topview is not None
            assert orchestrator.heygen is not None
            assert orchestrator.discord is not None
            
            # 5. Verificar dashboard
            assert dashboard_state is not None
            
            print("✅ Integração completa funcionando")
            
        except Exception as e:
            pytest.fail(f"Integração completa falhou: {e}")


# ────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO DOS TESTES
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Executar testes com pytest
    pytest.main([__file__, "-v", "-s"])
