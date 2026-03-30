import asyncio
from typing import Dict, Any
from loguru import logger
from src.llm.factory import LLMFactory

class ScriptGenerator:
    """
    Gera roteiros de alta conversão baseados nas tendências descobertas.
    """
    
    def __init__(self, llm=None):
        self.llm = llm
        
    async def generate_script(self, country: str, vertical: str, language: str, trend_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera um roteiro UGC-style baseado nas tendências.
        """
        logger.info(f"✍️ Gerando roteiro para {vertical} no(a) {country} baseado em tendências...")
        
        # Extrair dados da tendência
        topic = trend_data.get("trending_topic", "")
        pain_points = ", ".join(trend_data.get("pain_points", []))
        hooks = ", ".join(trend_data.get("viral_hooks", []))
        cultural_context = trend_data.get("cultural_context", "")
        
        # Mapeamento de idiomas para o formato Topview
        lang_map = {
            "Português": "pt",
            "Inglês": "en",
            "Espanhol": "es",
            "Alemão": "de",
            "Italiano": "it"
        }
        topview_lang = lang_map.get(language, "en")
        
        prompt = f"""
        Você é um copywriter de elite especializado em vídeos curtos (TikTok/Reels/Shorts) de alta conversão.
        Sua missão é criar um roteiro UGC (User Generated Content) que pareça 100% natural, como se fosse uma pessoa comum gravando com o celular.
        
        CONTEXTO DA TENDÊNCIA:
        - País: {country}
        - Idioma de saída: {language} (O ROTEIRO DEVE SER ESCRITO NESTE IDIOMA)
        - Vertical: {vertical}
        - Tópico em Alta: {topic}
        - Dores do Público: {pain_points}
        - Ganchos Virais Sugeridos: {hooks}
        - Contexto Cultural: {cultural_context}
        
        REGRAS DO ROTEIRO UGC:
        1. Duração: Exatamente 20-25 segundos (cerca de 50-60 palavras).
        2. Estilo: Conversacional, casual, autêntico. Use gírias locais leves se apropriado.
        3. Estrutura:
           - 0-3s: Hook (Gancho) que prende a atenção imediatamente tocando na dor.
           - 3-15s: Corpo (Apresenta a solução/produto de forma natural, como uma descoberta).
           - 15-25s: CTA (Chamada para ação clara e urgente).
        4. Voz: Inclua pausas naturais (ex: "ééé...", "sabe?", "tipo assim"). Não deve parecer lido.
        5. Conformidade: NÃO faça promessas falsas de dinheiro fácil ou cura milagrosa (evitar ban no Google/FB Ads).
        
        Retorne APENAS um JSON válido com a seguinte estrutura:
        {{
            "script_text": "O texto exato que o avatar vai falar (no idioma {language})",
            "visual_instructions": "Instruções de como o vídeo deve parecer (cenário, emoção do avatar)",
            "on_screen_text": "Texto curto para aparecer na tela durante o vídeo (no idioma {language})",
            "topview_lang": "{topview_lang}"
        }}
        """
        
        try:
            response = await self.llm.generate_text(prompt)
            
            # Limpar a resposta para garantir que é um JSON válido
            import json
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
                
            script_data = json.loads(response.strip())
            logger.success(f"✅ Roteiro gerado com sucesso!")
            return script_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar roteiro: {str(e)}")
            # Fallback seguro
            return {
                "script_text": f"Hey! I just found this amazing {topic}. You have to check it out right now! Link in bio.",
                "visual_instructions": "Casual setting, holding phone, excited expression.",
                "on_screen_text": f"Best {topic} ever! 🔥"
            }
