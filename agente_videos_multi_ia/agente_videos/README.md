# 🎬 Agente de Vídeos Unificado - Super-Agente UGC

**Versão:** 1.0.0-unified  
**Status:** ✅ Pronto para Produção  
**Data de Unificação:** 30 de Março de 2026

---

## 📋 Visão Geral

Um **super-agente inteligente** que combina pesquisa de tendências em tempo real, geração automática de vídeos UGC, bot Discord para controle manual e orquestração híbrida. Suporta múltiplos modos de operação e integra-se perfeitamente com Topview, HeyGen, ElevenLabs e Google Workspace.

### Principais Características

✅ **3 Modos de Operação**
- **AUTO**: Pesquisa tendências automaticamente e gera vídeos
- **MANUAL**: Lê tarefas do Google Sheets via bot Discord
- **HYBRID**: Ambos em paralelo

✅ **Pesquisa de Tendências em Tempo Real**
- Google Trends + TikTok + Análise IA
- Contexto cultural por país
- Seleção automática de vertical

✅ **Geração Inteligente de Vídeos**
- Topview (Avatar Marketing Video) como principal
- HeyGen como fallback automático
- ElevenLabs para áudio multilíngue
- Retry automático com backoff exponencial

✅ **Bot Discord Completo**
- `/gerar_video` - Criar vídeo sob demanda
- `/status` - Verificar status do agente
- `/tendencias` - Pesquisar tendências
- Aprovação por reações (✅/❌)

✅ **Dashboard em Tempo Real**
- Métricas de vídeos (gerados, aprovados, rejeitados)
- Tendências descobertas
- Tarefas em processamento
- Rastreamento de vídeos Topview
- Log de atividades
- Estatísticas gerais

✅ **Multi-LLM Support**
- GPT-4o
- Claude Sonnet 4.6
- Gemini 2.5 Flash
- Fallback automático

✅ **Resiliência e Confiabilidade**
- Retry automático com backoff exponencial
- Cache de resultados (24h TTL)
- Logging profissional com Loguru
- Tratamento robusto de erros

---

## 🏗️ Arquitetura

```
agente_videos_unified/
│
├── 📁 src/
│   ├── core/                    # Núcleo do agente
│   │   ├── orchestrator.py      # Orquestrador original (backup)
│   │   ├── orchestrator_hybrid.py  # Orquestrador híbrido (NOVO)
│   │   └── script_generator.py  # Gerador de roteiros
│   │
│   ├── research/
│   │   └── trend_analyzer.py    # Análise de tendências
│   │
│   ├── integrations/            # Integrações com APIs
│   │   ├── topview_client.py    # Topview (principal)
│   │   ├── heygen_client.py     # HeyGen (fallback)
│   │   ├── elevenlabs_client.py # ElevenLabs (áudio)
│   │   └── discord_client.py    # Discord (aprovação)
│   │
│   ├── api/
│   │   ├── server.py            # Dashboard original (backup)
│   │   ├── server_unified.py    # Dashboard unificado (NOVO)
│   │   └── templates/
│   │       └── index.html       # UI
│   │
│   ├── llm/
│   │   ├── factory.py           # Factory pattern
│   │   ├── base_llm.py          # Interface base
│   │   └── providers/           # GPT, Claude, Gemini
│   │
│   └── utils/
│       ├── config.py            # Carregamento de config
│       ├── retry.py             # Retry automático
│       ├── cache.py             # Cache de resultados
│       └── video_processor.py   # Pós-processamento
│
├── 📁 discord_bot/              # Bot Discord refatorado
│   ├── bot.py                   # Bot principal (NOVO)
│   ├── bot_original.py          # Bot original (backup)
│   ├── commands/                # Comandos
│   └── handlers/                # Handlers de eventos
│
├── 📁 config/
│   ├── settings.yaml            # Configurações
│   └── google_credentials.json  # Credenciais Google
│
├── 📁 tests/
│   └── test_integration.py      # Suite de testes (22 testes ✅)
│
├── 📁 logs/
├── 📁 temp_audio/
├── 📁 temp_video/
│
├── main.py                      # Ponto de entrada original
├── requirements.txt             # Dependências
├── .env                         # Variáveis de ambiente
└── README.md                    # Este arquivo
```

---

## 🚀 Instalação e Setup

### Pré-requisitos

- Python 3.10+
- pip ou conda
- Variáveis de ambiente configuradas (.env)

### Passo 1: Clonar/Copiar Projeto

```bash
# Se estiver em um repositório git
git clone <seu-repo>
cd agente_videos_unified

# Ou copiar a pasta existente
cp -r /home/ubuntu/agente_videos_unified ./
cd agente_videos_unified
```

### Passo 2: Criar Ambiente Virtual (Opcional mas Recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Configurar Variáveis de Ambiente

Criar arquivo `.env` na raiz do projeto:

```bash
# OpenAI
OPENAI_API_KEY=sk-sua-chave-aqui

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui

# Google
GOOGLE_API_KEY=sua-chave-gemini-aqui
GOOGLE_SHEETS_ID=seu-sheets-id-aqui
GOOGLE_DRIVE_FOLDER_ID=seu-folder-id-aqui

# ElevenLabs
ELEVENLABS_API_KEY=sua-chave-aqui

# Topview
TOPVIEW_API_KEY=sua-chave-aqui
TOPVIEW_UID=seu-uid-aqui

# Discord
DISCORD_BOT_TOKEN=seu-token-aqui
DISCORD_CHANNEL_ID=seu-channel-id-aqui

# HeyGen (Opcional)
HEYGEN_API_KEY=sua-chave-aqui
```

### Passo 5: Testar Instalação

```bash
python3 -m pytest tests/test_integration.py -v
```

Resultado esperado: **22/22 testes passando** ✅

---

## 📖 Como Usar

### Modo 1: Agente Automático (Pesquisa Tendências)

```bash
python main.py --agent-only
```

O agente irá:
1. Pesquisar tendências a cada 60 minutos
2. Gerar roteiros com IA
3. Criar vídeos com Topview
4. Enviar para aprovação no Discord
5. Salvar no Google Drive

### Modo 2: Bot Discord (Controle Manual)

```bash
python discord_bot/bot.py
```

Comandos disponíveis no Discord:

```
/gerar_video pais=Brasil vertical=Finanças idioma=Português
/status
/tendencias pais=Brasil
```

### Modo 3: Híbrido (Recomendado)

```bash
python main.py
```

Roda **ambos em paralelo**:
- Bot Discord aguardando comandos
- Agente pesquisando tendências automaticamente
- Dashboard em `http://localhost:8000`

### Modo 4: Teste Rápido

```bash
python main.py --run-once --agent-only
```

Executa um ciclo e encerra (ideal para testes).

---

## 🎮 Usando o Dashboard

Acesse `http://localhost:8000` para visualizar:

### 📊 Métricas
- Vídeos gerados hoje
- Taxa de aprovação
- Tempo médio de processamento

### 🔥 Tendências
- Tópicos em alta
- Crescimento de buscas
- Contexto cultural

### 📋 Tarefas Ativas
- Tarefas em processamento
- Progresso de cada uma
- Status em tempo real

### 🎥 Topview Tasks
- Rastreamento de vídeos
- Progresso de geração
- Status de cada tarefa

### 🎬 Vídeos Recentes
- Últimos 10 vídeos gerados
- Status (aprovado/rejeitado)
- Links para visualização

### 🤖 Atividades Discord
- Comandos executados
- Usuários que executaram
- Status de cada comando

### 📝 Log de Atividades
- Eventos gerais do sistema
- Timestamps
- Módulos envolvidos

---

## 🔧 Configuração Avançada

### Alterar Modo de Operação

Editar `config/settings.yaml`:

```yaml
execution:
  mode: "hybrid"  # auto, manual, hybrid
  interval_minutes: 60
  max_parallel_tasks: 3
  retry_attempts: 3
```

### Alterar Provedor LLM

```yaml
llm:
  provider: "gemini"  # gpt, claude, gemini
  providers:
    gpt:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4o"
    claude:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-sonnet-4-6"
    gemini:
      api_key: "${GOOGLE_API_KEY}"
      model: "gemini-2.5-flash"
```

### Configurar Avatares por Vertical

No `orchestrator_hybrid.py`, método `_select_avatar_voice()`:

```python
def _select_avatar_voice(self, vertical: str) -> tuple:
    if "Finanç" in vertical:
        return ("avatar_professional_01", "voice_professional_trust")
    elif "Shein" in vertical:
        return ("avatar_influencer_02", "voice_casual_excited")
    # ... adicionar mais verticais
```

---

## 🧪 Testes

### Executar Todos os Testes

```bash
python3 -m pytest tests/ -v
```

### Executar Testes Específicos

```bash
# Testes de imports
pytest tests/test_integration.py::TestImports -v

# Testes do orquestrador
pytest tests/test_integration.py::TestOrchestrator -v

# Testes do dashboard
pytest tests/test_integration.py::TestDashboard -v
```

### Cobertura de Testes

```bash
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 Estrutura de Dados

### Estado do Dashboard

```python
dashboard_state = {
    "status": "🟢 Online",
    "modo_operacao": "hybrid",
    "metricas": {
        "videos_gerados_hoje": 0,
        "videos_aprovados": 0,
        "videos_rejeitados": 0,
        "taxa_aprovacao": 0.0,
    },
    "tendencias": [...],
    "tarefas_ativas": {...},
    "topview_tasks": {...},
    "videos_recentes": [...],
    "atividades_discord": [...],
    "log_atividades": [...],
    "stats": {...}
}
```

### Tarefa de Vídeo

```python
task = {
    "id": "task_001",
    "pais": "Brasil",
    "vertical": "Finanças",
    "idioma": "Português",
    "prompt_extra": "Focar em pessoas com score baixo",
    "source": "auto"  # ou "manual"
}
```

---

## 🐛 Troubleshooting

### Problema: Bot não conecta no Discord

**Solução:**
```bash
# Verificar token
echo $DISCORD_BOT_TOKEN

# Verificar permissões do bot no servidor
# - Enviar mensagens
# - Ler histórico
# - Adicionar reações
```

### Problema: Erro ao ler Google Sheets

**Solução:**
```bash
# Verificar arquivo de credenciais
ls -la config/google_credentials.json

# Verificar GOOGLE_SHEETS_ID
echo $GOOGLE_SHEETS_ID
```

### Problema: Topview retorna erro 401

**Solução:**
```bash
# Verificar credenciais
echo $TOPVIEW_API_KEY
echo $TOPVIEW_UID

# Testar conexão
curl -H "Authorization: Bearer $TOPVIEW_API_KEY" \
     -H "Topview-Uid: $TOPVIEW_UID" \
     https://api.topview.ai/v1/m2v/task/query?taskId=test
```

### Problema: Dashboard não carrega

**Solução:**
```bash
# Verificar se servidor está rodando
curl http://localhost:8000

# Verificar logs
tail -f logs/agente_*.log
```

---

## 📈 Performance e Otimizações

### Cache

O agente cacheia:
- Resultados de tendências (24h)
- Scripts gerados (24h)
- Respostas de LLM (24h)

Para limpar cache:
```bash
rm logs/cache.json
```

### Retry Automático

Configurar em `config/settings.yaml`:
```yaml
execution:
  retry_attempts: 3
  retry_delay_seconds: 10
```

### Processamento Paralelo

Até 3 vídeos simultâneos:
```yaml
execution:
  max_parallel_tasks: 3
```

---

## 🚀 Deployment

### Docker

```bash
# Criar imagem
docker build -t agente-videos:1.0 .

# Rodar container
docker run -d \
  --name agente-videos \
  -p 8000:8000 \
  -e DISCORD_BOT_TOKEN=seu-token \
  -e TOPVIEW_API_KEY=sua-chave \
  agente-videos:1.0
```

### Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
```

### Railway/Heroku

```bash
# Fazer push para git
git push heroku main

# Verificar logs
heroku logs --tail
```

---

## 📝 Logging

Logs são salvos em `logs/`:

```
logs/
├── agente_2026-03-30_00-10-15.log
├── bot_2026-03-30_00-10-15.log
└── cache.json
```

### Níveis de Log

- `DEBUG` - Informações detalhadas
- `INFO` - Informações gerais
- `WARNING` - Avisos
- `ERROR` - Erros
- `CRITICAL` - Erros críticos

---

## 🤝 Contribuindo

### Adicionar Nova Vertical

1. Editar `orchestrator_hybrid.py`
2. Adicionar no método `_select_avatar_voice()`
3. Testar com `pytest`

### Adicionar Novo Provedor LLM

1. Criar `src/llm/providers/novo_provider.py`
2. Herdar de `BaseLLM`
3. Implementar `generate_script()` e `analyze_trend()`
4. Registrar no `factory.py`

### Adicionar Novo Comando Discord

1. Criar `discord_bot/commands/novo_comando.py`
2. Adicionar handler em `bot.py`
3. Testar com bot de teste

---

## 📚 Referências

- [Topview API Docs](https://docs.topview.ai)
- [HeyGen API Docs](https://docs.heygen.com)
- [ElevenLabs API Docs](https://elevenlabs.io/docs)
- [Discord.py Docs](https://discordpy.readthedocs.io)
- [FastAPI Docs](https://fastapi.tiangolo.com)

---

## 📄 Licença

Proprietário - Uso interno apenas

---

## 👥 Suporte

Para dúvidas ou problemas, consulte:

1. **Documentação**: `/home/ubuntu/GUIA_INTEGRACAO_PROJETOS.md`
2. **Análise Comparativa**: `/home/ubuntu/ANALISE_PROJETOS_COMPARATIVA.md`
3. **Plano de Unificação**: `/home/ubuntu/PLANO_UNIFICACAO_DETALHADO.md`
4. **Testes**: `pytest tests/test_integration.py -v`

---

## 🎉 Conclusão

Você agora tem um **super-agente unificado** profissional, testado e pronto para produção! 

**Próximos passos:**
1. Configurar credenciais no `.env`
2. Testar com `pytest`
3. Rodar em modo híbrido: `python main.py`
4. Acessar dashboard em `http://localhost:8000`
5. Usar bot Discord para criar vídeos

Boa sorte! 🚀
