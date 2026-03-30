# ⚡ Guia de Início Rápido

Comece a usar o agente em **5 minutos**!

---

## 1️⃣ Setup Inicial (2 minutos)

```bash
# Clonar/Copiar projeto
cd /home/ubuntu/agente_videos_unified

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo .env
cp .env.example .env
# Editar .env com suas credenciais
```

---

## 2️⃣ Configurar Credenciais (1 minuto)

Editar `.env`:

```bash
# Obrigatório
OPENAI_API_KEY=sk-...
DISCORD_BOT_TOKEN=...
TOPVIEW_API_KEY=...

# Opcional (fallback)
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
ELEVENLABS_API_KEY=...
```

---

## 3️⃣ Testar Instalação (1 minuto)

```bash
# Rodar testes
python3 -m pytest tests/test_integration.py -v

# Esperado: 22/22 testes passando ✅
```

---

## 4️⃣ Iniciar Agente (1 minuto)

### Opção A: Modo Automático (Recomendado)

```bash
python main.py
```

Isso vai:
- ✅ Iniciar bot Discord
- ✅ Iniciar dashboard em http://localhost:8000
- ✅ Começar a pesquisar tendências automaticamente

### Opção B: Teste Rápido

```bash
python main.py --run-once --agent-only
```

Executa um ciclo e encerra.

### Opção C: Apenas Bot Discord

```bash
python discord_bot/bot.py
```

---

## 5️⃣ Usar o Agente

### Via Dashboard

Acesse: **http://localhost:8000**

Veja em tempo real:
- 📊 Métricas
- 🔥 Tendências
- 📋 Tarefas
- 🎬 Vídeos

### Via Discord

```
/gerar_video pais=Brasil vertical=Finanças idioma=Português
/status
/tendencias pais=Brasil
```

---

## 🎯 Próximos Passos

1. **Configurar Google Sheets** (opcional)
   - Adicionar `GOOGLE_SHEETS_ID` no `.env`
   - Criar planilha com tarefas

2. **Personalizar Avatares**
   - Editar `src/core/orchestrator_hybrid.py`
   - Método `_select_avatar_voice()`

3. **Adicionar Mais Verticais**
   - Editar `config/settings.yaml`
   - Adicionar em `verticais`

4. **Monitorar Logs**
   - `tail -f logs/agente_*.log`

---

## 🆘 Problemas Comuns

| Problema | Solução |
|----------|---------|
| Bot não conecta | Verificar `DISCORD_BOT_TOKEN` |
| Topview erro 401 | Verificar `TOPVIEW_API_KEY` |
| Dashboard não carrega | `curl http://localhost:8000` |
| Testes falhando | `pip install -r requirements.txt` |

---

## 📞 Suporte

- 📖 README completo: `README.md`
- 🔍 Análise técnica: `/home/ubuntu/ANALISE_PROJETOS_COMPARATIVA.md`
- 📋 Plano detalhado: `/home/ubuntu/PLANO_UNIFICACAO_DETALHADO.md`

---

**Pronto! Você está rodando o agente! 🚀**
