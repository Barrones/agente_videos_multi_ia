import json
from typing import Dict, Any
from openai import AsyncOpenAI
from .base import BaseIntegration

class OpenAIIntegration(BaseIntegration):
    def _setup(self):
        api_key = self.config.get("apis", {}).get("openai", {}).get("api_key")
        self.model = self.config.get("apis", {}).get("openai", {}).get("model", "gpt-4o")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        if not self.client:
            self.logger.warning("OpenAI API Key não configurada. Usando modo mock.")

    async def generate_script(self, task_data: Dict[str, Any]) -> Dict[str, str]:
        """Gera o roteiro de alta conversão baseado nos dados da tarefa"""
        if not self.client:
            self.logger.info("Modo Mock: Gerando roteiro simulado")
            return {
                "gancho": f"Gancho simulado para {task_data.get('pais')}",
                "roteiro_completo": f"Roteiro completo simulado em {task_data.get('idioma')}",
                "cenario": "Cenário simulado"
            }

        prompt = f"""Você é um especialista em copywriting de alta conversão para vídeos de 25 segundos.
Crie um roteiro EXATAMENTE no formato abaixo, sem desvios:

País: {task_data.get('pais')}
Idioma do Vídeo: {task_data.get('idioma')}
Vertical: {task_data.get('vertical')}
Dor/Foco: {task_data.get('prompt_base')}

REQUISITOS CRÍTICOS:
1. O roteiro deve ter EXATAMENTE 25 segundos de fala (aproximadamente 60-70 palavras).
2. Deve parecer natural, com pausas e hesitações ("ééé", "sabe?", "tipo").
3. Deve começar com um GANCHO que para o scroll (primeiros 3 segundos).
4. Deve focar na DOR do cliente, não apenas no produto.
5. Deve ter um CTA claro e direto no final.
6. NUNCA fazer promessas irreais (sem "100% garantido", "ganhe dinheiro", etc).
7. Usar palavras como "pode conseguir", "chance de", "verifique se".
8. O roteiro DEVE ser escrito NO IDIOMA {task_data.get('idioma')}, não em português.

RETORNE UM JSON EXATO:
{{
  "gancho": "Os primeiros 3 segundos que param o scroll (em {task_data.get('idioma')})",
  "dor": "Identificação do problema real (em {task_data.get('idioma')})",
  "solucao": "A solução/brecha (em {task_data.get('idioma')})",
  "prova_social": "Validação ou urgência (em {task_data.get('idioma')})",
  "cta": "Call to action direto (em {task_data.get('idioma')})",
  "roteiro_completo": "O texto COMPLETO que o avatar vai falar, em {task_data.get('idioma')}",
  "cenario": "Descrição visual do cenário e enquadramento em português"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.error(f"Erro ao gerar roteiro: {str(e)}")
            raise
