"""
Dashboard Unificado - FastAPI + Jinja2
Monitora: Tendências, Tarefas, Vídeos, Topview, Bot Discord
"""

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import json
import os
from datetime import datetime
from loguru import logger
from typing import Dict, Any, List, Optional

# Criar aplicação FastAPI
app = FastAPI(
    title="🎬 Agente de Vídeos Unificado - Dashboard",
    description="Dashboard em tempo real para agente de geração de vídeos UGC",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar templates
templates = Jinja2Templates(directory="src/api/templates")

# ────────────────────────────────────────────────────────────────────────────
# ESTADO GLOBAL DO DASHBOARD
# ────────────────────────────────────────────────────────────────────────────

dashboard_state = {
    # Status geral
    "status": "🟢 Online",
    "modo_operacao": "hybrid",  # auto, manual, hybrid
    "timestamp": datetime.now().isoformat(),
    
    # Métricas
    "metricas": {
        "videos_gerados_hoje": 0,
        "videos_aprovados": 0,
        "videos_rejeitados": 0,
        "taxa_aprovacao": 0.0,
        "tempo_medio_processamento": 0,
    },
    
    # Tendências descobertas
    "tendencias": [],  # [{"pais": "Brasil", "vertical": "Finanças", "topico": "Cartão", "crescimento": "+250%", "timestamp": "..."}]
    
    # Tarefas em processamento
    "tarefas_ativas": {},  # {task_id: {"status": "processando", "pais": "Brasil", "vertical": "Finanças", "progresso": 45}}
    
    # Tarefas do Topview
    "topview_tasks": {},  # {task_id: {"status": "processando", "avatar": "avatar_01", "progresso": 60, "updated_at": "..."}}
    
    # Vídeos gerados
    "videos_recentes": [],  # [{"id": "vid_001", "pais": "Brasil", "vertical": "Finanças", "status": "aprovado", "url": "...", "timestamp": "..."}]
    
    # Atividades do Bot Discord
    "atividades_discord": [],  # [{"tipo": "comando", "usuario": "user#1234", "comando": "/gerar_video", "status": "sucesso", "timestamp": "..."}]
    
    # Log de atividades geral
    "log_atividades": [],  # [{"timestamp": "...", "nivel": "INFO", "mensagem": "...", "modulo": "..."}]
    
    # Estatísticas
    "stats": {
        "total_vídeos_gerados": 0,
        "total_vídeos_aprovados": 0,
        "total_tendências_descobertas": 0,
        "tempo_total_processamento": 0,
        "uptime_horas": 0,
    }
}

# ────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Página principal do dashboard"""
    return templates.TemplateResponse("index_unified.html", {
        "request": request,
        "state": dashboard_state
    })


@app.get("/api/status")
async def get_status():
    """Retorna status geral do agente"""
    dashboard_state["timestamp"] = datetime.now().isoformat()
    return dashboard_state


@app.get("/api/metricas")
async def get_metricas():
    """Retorna métricas do agente"""
    return dashboard_state["metricas"]


@app.get("/api/tendencias")
async def get_tendencias():
    """Retorna tendências descobertas"""
    return dashboard_state["tendencias"]


@app.get("/api/tarefas-ativas")
async def get_tarefas_ativas():
    """Retorna tarefas em processamento"""
    return dashboard_state["tarefas_ativas"]


@app.get("/api/topview-tasks")
async def get_topview_tasks():
    """Retorna tarefas do Topview"""
    return dashboard_state["topview_tasks"]


@app.get("/api/videos-recentes")
async def get_videos_recentes():
    """Retorna vídeos gerados recentemente"""
    return dashboard_state["videos_recentes"]


@app.get("/api/atividades-discord")
async def get_atividades_discord():
    """Retorna atividades do bot Discord"""
    return dashboard_state["atividades_discord"]


@app.get("/api/log-atividades")
async def get_log_atividades(limit: int = 50):
    """Retorna log de atividades"""
    return dashboard_state["log_atividades"][:limit]


@app.get("/api/stats")
async def get_stats():
    """Retorna estatísticas gerais"""
    return dashboard_state["stats"]


# ────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE ATUALIZAÇÃO (chamadas pelo orquestrador)
# ────────────────────────────────────────────────────────────────────────────

def update_metricas(videos_gerados: Optional[int] = None, videos_aprovados: Optional[int] = None, 
                   videos_rejeitados: Optional[int] = None):
    """Atualiza métricas do dashboard"""
    if videos_gerados is not None:
        dashboard_state["metricas"]["videos_gerados_hoje"] = videos_gerados
    
    if videos_aprovados is not None:
        dashboard_state["metricas"]["videos_aprovados"] = videos_aprovados
    
    if videos_rejeitados is not None:
        dashboard_state["metricas"]["videos_rejeitados"] = videos_rejeitados
    
    # Calcular taxa de aprovação
    total = videos_aprovados + videos_rejeitados if videos_aprovados and videos_rejeitados else 1
    dashboard_state["metricas"]["taxa_aprovacao"] = (videos_aprovados / total * 100) if videos_aprovados else 0


def add_tendencia(pais: str, vertical: str, topico: str, crescimento: str, detalhes: Dict[str, Any] = None):
    """Adiciona uma nova tendência ao dashboard"""
    tendencia = {
        "id": f"trend_{datetime.now().timestamp()}",
        "pais": pais,
        "vertical": vertical,
        "topico": topico,
        "crescimento": crescimento,
        "timestamp": datetime.now().isoformat(),
        "detalhes": detalhes or {}
    }
    
    dashboard_state["tendencias"].insert(0, tendencia)
    
    # Manter apenas as 20 tendências mais recentes
    if len(dashboard_state["tendencias"]) > 20:
        dashboard_state["tendencias"].pop()
    
    # Incrementar contador de tendências
    dashboard_state["stats"]["total_tendências_descobertas"] += 1
    
    logger.info(f"🔥 Tendência adicionada: {pais} - {vertical} - {topico}")


def add_tarefa_ativa(task_id: str, pais: str, vertical: str, status: str = "iniciando"):
    """Adiciona uma tarefa ativa ao dashboard"""
    dashboard_state["tarefas_ativas"][task_id] = {
        "id": task_id,
        "pais": pais,
        "vertical": vertical,
        "status": status,
        "progresso": 0,
        "timestamp_inicio": datetime.now().isoformat()
    }
    
    logger.info(f"📋 Tarefa ativa adicionada: {task_id}")


def update_tarefa_ativa(task_id: str, status: str, progresso: int = 0):
    """Atualiza o status de uma tarefa ativa"""
    if task_id in dashboard_state["tarefas_ativas"]:
        dashboard_state["tarefas_ativas"][task_id]["status"] = status
        dashboard_state["tarefas_ativas"][task_id]["progresso"] = progresso
        logger.info(f"📊 Tarefa {task_id} atualizada: {status} ({progresso}%)")


def remove_tarefa_ativa(task_id: str):
    """Remove uma tarefa ativa do dashboard"""
    if task_id in dashboard_state["tarefas_ativas"]:
        del dashboard_state["tarefas_ativas"][task_id]
        logger.info(f"✅ Tarefa {task_id} removida de ativas")


def add_topview_task(task_id: str, avatar: str, status: str = "submetido"):
    """Adiciona uma tarefa do Topview ao dashboard"""
    dashboard_state["topview_tasks"][task_id] = {
        "id": task_id,
        "avatar": avatar,
        "status": status,
        "progresso": 0,
        "updated_at": datetime.now().isoformat()
    }
    
    logger.info(f"🎥 Tarefa Topview adicionada: {task_id}")


def update_topview_task(task_id: str, status: str, progresso: int = 0, detalhes: str = ""):
    """Atualiza o status de uma tarefa do Topview"""
    if task_id in dashboard_state["topview_tasks"]:
        dashboard_state["topview_tasks"][task_id]["status"] = status
        dashboard_state["topview_tasks"][task_id]["progresso"] = progresso
        dashboard_state["topview_tasks"][task_id]["updated_at"] = datetime.now().isoformat()
        if detalhes:
            dashboard_state["topview_tasks"][task_id]["detalhes"] = detalhes
        logger.info(f"🎬 Topview {task_id}: {status} ({progresso}%)")


def add_video_recente(video_id: str, pais: str, vertical: str, status: str, url: str, script: str = ""):
    """Adiciona um vídeo gerado recentemente ao dashboard"""
    video = {
        "id": video_id,
        "pais": pais,
        "vertical": vertical,
        "status": status,
        "url": url,
        "script": script[:200] + "..." if len(script) > 200 else script,
        "timestamp": datetime.now().isoformat()
    }
    
    dashboard_state["videos_recentes"].insert(0, video)
    
    # Manter apenas os 10 vídeos mais recentes
    if len(dashboard_state["videos_recentes"]) > 10:
        dashboard_state["videos_recentes"].pop()
    
    # Incrementar contador
    dashboard_state["stats"]["total_vídeos_gerados"] += 1
    if status == "aprovado":
        dashboard_state["stats"]["total_vídeos_aprovados"] += 1
    
    logger.info(f"🎬 Vídeo adicionado: {video_id} - {status}")


def add_atividade_discord(tipo: str, usuario: str, comando: str, status: str, detalhes: str = ""):
    """Adiciona uma atividade do bot Discord ao dashboard"""
    atividade = {
        "tipo": tipo,
        "usuario": usuario,
        "comando": comando,
        "status": status,
        "detalhes": detalhes,
        "timestamp": datetime.now().isoformat()
    }
    
    dashboard_state["atividades_discord"].insert(0, atividade)
    
    # Manter apenas as 20 atividades mais recentes
    if len(dashboard_state["atividades_discord"]) > 20:
        dashboard_state["atividades_discord"].pop()
    
    logger.info(f"🤖 Atividade Discord: {usuario} - {comando} - {status}")


def add_log_atividade(nivel: str, mensagem: str, modulo: str = "agente"):
    """Adiciona uma atividade ao log geral"""
    atividade = {
        "timestamp": datetime.now().isoformat(),
        "nivel": nivel,
        "mensagem": mensagem,
        "modulo": modulo
    }
    
    dashboard_state["log_atividades"].insert(0, atividade)
    
    # Manter apenas os 100 logs mais recentes
    if len(dashboard_state["log_atividades"]) > 100:
        dashboard_state["log_atividades"].pop()


def set_modo_operacao(modo: str):
    """Define o modo de operação do agente"""
    dashboard_state["modo_operacao"] = modo
    logger.info(f"🔄 Modo de operação alterado para: {modo}")


def set_status(status: str):
    """Define o status geral do agente"""
    dashboard_state["status"] = status
    logger.info(f"📊 Status alterado para: {status}")


# ────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO DO SERVIDOR
# ────────────────────────────────────────────────────────────────────────────

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Inicia o servidor FastAPI em uma thread separada"""
    
    def run():
        logger.info(f"🚀 Iniciando Dashboard em http://{host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="warning")
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    
    logger.info("✅ Dashboard iniciado em thread separada")
    return thread


# ────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("🎬 Iniciando Agente de Vídeos - Dashboard")
    start_server()
    
    # Manter a aplicação rodando
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Dashboard encerrado")
