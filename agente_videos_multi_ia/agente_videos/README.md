# 🎬 Agente de Vídeos de Alta Conversão (Python)

Um agente autônomo profissional construído em Python para orquestrar a geração de vídeos de alta conversão em escala. Ele integra OpenAI, ElevenLabs, Topview.ai e Discord para criar um pipeline completo de produção de conteúdo.

## 🌟 Recursos Extraordinários

- **Orquestração Inteligente**: Processamento assíncrono com `asyncio` para máxima performance.
- **Processamento Paralelo**: Gera múltiplos vídeos simultaneamente (configurável via `max_parallel_tasks`).
- **Dashboard em Tempo Real**: Interface web (FastAPI) para monitorar o status do agente.
- **Sistema de Cache**: Evita reprocessamento e economiza créditos de API.
- **Retry Automático**: Resiliência contra falhas de rede usando `tenacity`.
- **Logging Profissional**: Rastreamento completo com `loguru`.
- **Configuração Flexível**: Gerenciamento via YAML e variáveis de ambiente.

## 📂 Estrutura do Projeto

```text
agente_videos/
├── config/
│   └── settings.yaml          # Configurações principais
├── src/
│   ├── api/                   # Dashboard FastAPI
│   │   ├── server.py
│   │   └── templates/
│   ├── core/                  # Lógica principal
│   │   └── orchestrator.py
│   ├── integrations/          # Clientes de API
│   │   ├── base.py
│   │   ├── openai_client.py
│   │   ├── elevenlabs_client.py
│   │   ├── topview_client.py
│   │   └── discord_client.py
│   └── utils/                 # Utilitários
│       ├── config.py
│       ├── cache.py
│       └── retry.py
├── logs/                      # Arquivos de log gerados automaticamente
├── temp_audio/                # Arquivos de áudio temporários
├── main.py                    # Ponto de entrada
├── requirements.txt           # Dependências
└── .env                       # Variáveis de ambiente (crie o seu)
```

## 🚀 Guia de Setup (Passo a Passo)

### 1. Preparar o Ambiente

Certifique-se de ter o Python 3.10+ instalado.

```bash
# Clone ou acesse o diretório do projeto
cd agente_videos

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (`agente_videos/.env`) e adicione suas chaves:

```env
OPENAI_API_KEY=sk-sua-chave-aqui
ELEVENLABS_API_KEY=sua-chave-aqui
TOPVIEW_API_KEY=sua-chave-aqui
TOPVIEW_UID=seu-uid-aqui
DISCORD_BOT_TOKEN=seu-token-aqui
DISCORD_CHANNEL_ID=seu-id-aqui
```

### 3. Ajustar Configurações (Opcional)

Edite o arquivo `config/settings.yaml` para ajustar o comportamento do agente:
- `interval_minutes`: Tempo entre cada ciclo de execução.
- `max_parallel_tasks`: Quantos vídeos gerar ao mesmo tempo.
- `default_voice_id`: O ID da voz padrão do ElevenLabs.

### 4. Executar o Agente

Você pode rodar o agente de duas formas:

**Modo Único (Testes):**
Executa um ciclo e encerra.
```bash
python main.py --run-once
```

**Modo Contínuo (Produção):**
Roda indefinidamente, respeitando o intervalo configurado.
```bash
python main.py
```

### 5. Acessar o Dashboard

Com o agente rodando, abra seu navegador e acesse:
👉 **http://localhost:8000**

Você verá o painel em tempo real com estatísticas e logs de atividade.

## 🛠️ Como Estender (Para Desenvolvedores)

Para adicionar uma nova integração (ex: Google Sheets):
1. Crie um novo arquivo em `src/integrations/google_sheets.py`.
2. Herde de `BaseIntegration`.
3. Implemente os métodos necessários.
4. Instancie a classe no `VideoAgentOrchestrator` (`src/core/orchestrator.py`).

## 🛡️ Tratamento de Erros

O sistema usa o decorator `@with_retry` (em `src/utils/retry.py`) para lidar automaticamente com instabilidades de rede nas chamadas de API. Se uma API falhar, o agente tentará novamente com backoff exponencial antes de desistir.
