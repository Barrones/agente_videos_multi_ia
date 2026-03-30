# 🧠 Guia: Como Trocar de IA (Sistema Multi-LLM)

O Agente de Vídeos agora possui uma arquitetura **Plugin-Based** para Inteligência Artificial. Isso significa que você não está preso à OpenAI! Você pode trocar o "cérebro" do agente a qualquer momento, sem precisar alterar nenhuma linha de código.

## 🔄 Como Trocar a IA Ativa

Toda a configuração é feita no arquivo `config/settings.yaml`.

### Passo 1: Abra o arquivo de configuração
No VS Code, abra o arquivo `config/settings.yaml`.

### Passo 2: Altere o provedor
Procure a seção `llm:` e altere o valor de `provider`:

```yaml
llm:
  provider: "claude" # Mude aqui! Opções: gpt, claude, gemini, manus, copilot
```

### Passo 3: Configure a chave da API
Certifique-se de que a chave da API correspondente está no seu arquivo `.env`:

```env
# Arquivo .env
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="AIza..."
```

## 🤖 IAs Suportadas Atualmente

| Provedor | Modelo Padrão | Quando Usar? |
|----------|---------------|--------------|
| **gpt** | `gpt-4o` | Melhor equilíbrio geral. Ótimo para seguir instruções complexas. |
| **claude** | `claude-3-5-sonnet` | **Recomendado para UGC!** A escrita do Claude é a mais natural e humana, perfeita para roteiros conversacionais. |
| **gemini** | `gemini-2.5-flash` | Mais rápido e barato. Bom para testes em massa. |
| **manus** | `gpt-4.1-mini` | Se você tiver acesso à API do Manus. |
| **copilot** | `copilot-pro` | Integração futura. |

## 🛠️ Como Adicionar uma Nova IA no Futuro?

A arquitetura foi feita para ser escalável. Se amanhã lançarem o "GPT-5" ou uma IA totalmente nova (ex: Llama 3), você só precisa:

1. Criar um novo arquivo em `src/llm/providers/novo_provider.py`
2. Herdar da classe `BaseLLM`
3. Adicionar no `LLMFactory` (`src/llm/factory.py`)
4. Adicionar no `settings.yaml`

O resto do sistema (geração de voz, vídeo, aprovação no Discord) continuará funcionando perfeitamente, pois eles não se importam com *qual* IA gerou o roteiro, desde que o roteiro seja bom!

## 💡 Dica de Ouro para UGC

Para vídeos UGC (User Generated Content), **Claude 3.5 Sonnet** costuma gerar textos muito menos "robóticos" que o GPT-4. Ele usa gírias, pausas e hesitações de forma muito mais natural. Experimente trocar para `provider: "claude"` e veja a diferença na qualidade do roteiro!
