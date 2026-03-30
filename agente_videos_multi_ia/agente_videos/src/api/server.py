from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import threading
import json
import os
from loguru import logger

app = FastAPI(title="Agente de Vídeos - Dashboard")
templates = Jinja2Templates(directory="src/api/templates")

# Estado global simulado para o dashboard
agent_state = {
    "status": "Rodando",
    "videos_gerados_hoje": 0,
    "videos_aprovados": 0,
    "videos_rejeitados": 0,
    "ultimas_atividades": [],
    "tendencias_atuais": [],
    "tarefas_topview": {} # Rastreamento de tarefas do Topview
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": agent_state})

@app.get("/api/status")
async def get_status():
    return agent_state

def update_state(action: str, details: str):
    """Atualiza o estado global (chamado pelo orquestrador)"""
    agent_state["ultimas_atividades"].insert(0, {"action": action, "details": details})
    if len(agent_state["ultimas_atividades"]) > 50:
        agent_state["ultimas_atividades"].pop()

def add_trend(country: str, vertical: str, topic: str, growth: str):
    """Adiciona uma nova tendência descoberta ao dashboard"""
    agent_state["tendencias_atuais"].insert(0, {
        "country": country,
        "vertical": vertical,
        "topic": topic,
        "growth": growth
    })
    if len(agent_state["tendencias_atuais"]) > 10:
        agent_state["tendencias_atuais"].pop()

def update_topview_task(task_id: str, status: str, details: str = ""):
    """Atualiza o status de uma tarefa do Topview no dashboard"""
    agent_state["tarefas_topview"][task_id] = {
        "status": status,
        "details": details,
        "updated_at": os.popen('date "+%H:%M:%S"').read().strip()
    }

def start_server(host="0.0.0.0", port=8000):
    """Inicia o servidor em uma thread separada"""
    def run():
        logger.info(f"Iniciando Dashboard em http://{host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="warning")
        
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
