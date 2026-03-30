# 🔧 Extensões VS Code para Agente de Vídeos UGC

Aqui estão as extensões essenciais para trabalhar com o agente Python no VS Code. Todas são gratuitas!

## 📋 Extensões Recomendadas

### 1. **Python** (Microsoft)
**ID**: `ms-python.python`  
**Por que**: Suporte completo para Python (syntax highlighting, debugging, intellisense)

**Como instalar**:
1. Abra VS Code
2. Vá para Extensions (Ctrl+Shift+X)
3. Procure por "Python"
4. Clique em "Install" na extensão da Microsoft

### 2. **Pylance** (Microsoft)
**ID**: `ms-python.vscode-pylance`  
**Por que**: Intellisense avançado, type checking, autocompletar melhorado

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "Pylance"
3. Clique em "Install"

### 3. **Python Debugger** (Microsoft)
**ID**: `ms-python.debugpy`  
**Por que**: Debugar o código Python facilmente (breakpoints, step-by-step)

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "Python Debugger"
3. Clique em "Install"

### 4. **Prettier - Code Formatter** (Prettier)
**ID**: `esbenp.prettier-vscode`  
**Por que**: Formata código automaticamente (JSON, YAML, Markdown)

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "Prettier"
3. Clique em "Install"

### 5. **YAML** (Red Hat)
**ID**: `redhat.vscode-yaml`  
**Por que**: Suporte para arquivos YAML (config/settings.yaml)

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "YAML"
3. Clique em "Install"

### 6. **Thunder Client** (Thunder Client)
**ID**: `rangav.vscode-thunder-client`  
**Por que**: Testar APIs REST dentro do VS Code (alternativa ao Postman)

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "Thunder Client"
3. Clique em "Install"

### 7. **REST Client** (Huachao Mao)
**ID**: `humao.rest-client`  
**Por que**: Fazer requisições HTTP diretamente no VS Code

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "REST Client"
3. Clique em "Install"

### 8. **Git Graph** (mhutchie)
**ID**: `mhutchie.git-graph`  
**Por que**: Visualizar histórico Git de forma gráfica

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "Git Graph"
3. Clique em "Install"

### 9. **GitHub Copilot** (GitHub) - OPCIONAL
**ID**: `GitHub.copilot`  
**Por que**: IA que ajuda a escrever código (pago, mas vale a pena)

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "GitHub Copilot"
3. Clique em "Install"

### 10. **Markdown Preview Enhanced** (Yiyi Wang)
**ID**: `shd101wyy.markdown-preview-enhanced`  
**Por que**: Visualizar Markdown com preview melhorado

**Como instalar**:
1. Extensions (Ctrl+Shift+X)
2. Procure por "Markdown Preview Enhanced"
3. Clique em "Install"

---

## ⚡ Instalação Rápida (Copiar e Colar)

Se você quiser instalar tudo de uma vez via terminal, execute no VS Code (Ctrl+`):

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy
code --install-extension esbenp.prettier-vscode
code --install-extension redhat.vscode-yaml
code --install-extension rangav.vscode-thunder-client
code --install-extension humao.rest-client
code --install-extension mhutchie.git-graph
code --install-extension shd101wyy.markdown-preview-enhanced
```

---

## 🎯 Configurações Recomendadas

Após instalar as extensões, adicione isso no `settings.json` do VS Code:

**Como acessar**: Ctrl+Shift+P → "Preferences: Open Settings (JSON)"

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.pylintArgs": [
    "--max-line-length=120"
  ],
  "python.analysis.typeCheckingMode": "basic",
  "[yaml]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "editor.rulers": [80, 120],
  "editor.wordWrap": "on",
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true
  }
}
```

---

## 🚀 Próximos Passos

1. Instale as extensões acima
2. Abra o projeto `agente_videos/` no VS Code
3. Crie um arquivo `.env` na raiz com suas chaves de API
4. Abra o terminal (Ctrl+`) e execute:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
5. Execute o agente:
   ```bash
   python main.py --run-once
   ```

---

## 💡 Dicas Extras

- **Debugging**: Pressione F5 para iniciar o debugger
- **Terminal**: Ctrl+` para abrir/fechar terminal
- **Command Palette**: Ctrl+Shift+P para acessar todos os comandos
- **Git**: Ctrl+Shift+G para abrir Git
- **Extensions**: Ctrl+Shift+X para gerenciar extensões

Qualquer dúvida, é só chamar! 🎯
