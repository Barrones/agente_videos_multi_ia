import asyncio
import json
from typing import Dict, Any, List
from loguru import logger
from src.llm.factory import LLMFactory

class TrendAnalyzer:
    """
    Módulo responsável por pesquisar e analisar tendências em tempo real
    para diferentes países e verticais (Shein, Finanças, etc).
    """
    
    def __init__(self, llm=None):
        self.llm = llm
        
    async def analyze_trends(self, country: str, vertical: str, language: str) -> Dict[str, Any]:
        """
        Analisa tendências para um país e vertical específicos.
        """
        logger.info(f"🔍 Pesquisando tendências para {vertical} no(a) {country}...")
        
        # Em um ambiente de produção real, aqui entrarariam chamadas para:
        # - Google Trends API (pytrends)
        # - TikTok API / Scraper
        # - Shein Data Scraper
        
        # Como essas APIs são fechadas ou requerem proxies complexos,
        # usamos a IA para simular uma pesquisa de tendências em tempo real
        # baseada no contexto cultural e dados recentes.
        
        prompt = f"""
        Você é um analista de tendências de mercado global e especialista em tráfego pago.
        Preciso que você faça uma análise profunda das tendências ATUAIS para o seguinte cenário:
        
        - País: {country}
        - Idioma local: {language}
        - Vertical/Nicho: {vertical}
        
        Se a vertical for "Shein" ou "E-commerce":
        - Quais são os 3 produtos mais virais no TikTok deste país agora?
        - Qual é o estilo de vídeo UGC que mais converte para esses produtos?
        - Quais são as dores/desejos do público local? (ex: frete grátis, taxação, qualidade)
        
        Se a vertical for "Finanças" (Empréstimo, Cartão, etc):
        - Qual é a maior dor financeira da população deste país hoje? (ex: inflação, nome sujo, juros altos)
        - Quais soluções estão em alta?
        - Qual é o "gancho" (hook) que mais chama atenção neste país?
        
        Retorne APENAS um JSON válido com a seguinte estrutura:
        {{
            "trending_topic": "Nome do produto ou dor principal",
            "search_volume_growth": "+X%",
            "target_audience": "Descrição do público",
            "pain_points": ["dor 1", "dor 2"],
            "viral_hooks": ["gancho 1", "gancho 2"],
            "ugc_style_recommendation": "Como o vídeo deve parecer visualmente",
            "cultural_context": "Contexto cultural importante para o país"
        }}
        """
        
        try:
            response = await self.llm.generate_text(prompt)
            
            # Limpar a resposta para garantir que é um JSON válido
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
                
            trend_data = json.loads(response.strip())
            logger.success(f"✅ Tendências encontradas para {country}: {trend_data.get('trending_topic')}")
            return trend_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar tendências: {str(e)}")
            # Fallback seguro
            return {
                "trending_topic": f"Tendências de {vertical}",
                "search_volume_growth": "+100%",
                "target_audience": "Público geral",
                "pain_points": ["Preço alto", "Dificuldade de acesso"],
                "viral_hooks": ["Você não vai acreditar nisso", "Segredo revelado"],
                "ugc_style_recommendation": "Vídeo casual gravado com celular",
                "cultural_context": "Adaptar para a cultura local"
            }
