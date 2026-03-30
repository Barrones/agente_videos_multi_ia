"""
Bot Discord — Agente UGC
Gera script + audio + video por comando no Discord.
Pipeline: Gemini (script) → ElevenLabs (audio) → Topview (video) → Discord
"""

import discord
import asyncio
import os
import json
import aiohttp
import aiofiles
import warnings
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

warnings.filterwarnings("ignore")
load_dotenv()

DISCORD_TOKEN  = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID     = int(os.getenv("DISCORD_CHANNEL_ID"))
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
TOPVIEW_KEY    = os.getenv("TOPVIEW_API_KEY")
TOPVIEW_UID    = os.getenv("TOPVIEW_UID")
SHEET_ID       = os.getenv("GOOGLE_SHEETS_ID", "1PzBttxNEfhvnss-uuLqBM_fG_QRUFDBswIfsrHgTljg")
CREDS_FILE     = "config/google_credentials.json"

TOPVIEW_BASE   = "https://api.topview.ai/v1"
TOPVIEW_HEADERS = lambda: {
    "Authorization": f"Bearer {TOPVIEW_KEY}",
    "Topview-Uid": TOPVIEW_UID,
    "Content-Type": "application/json",
}

# ── Google Sheets ─────────────────────────────────────────────────────────────

def _sheets_service():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds).spreadsheets()

def sheets_ler_pendentes() -> list:
    """Retorna todas as linhas com status='pendente'"""
    try:
        sheet = _sheets_service()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range="A2:K1000").execute()
        rows = result.get("values", [])
        pendentes = []
        for i, row in enumerate(rows):
            while len(row) < 11:
                row.append("")
            if row[7].strip().lower() == "pendente":
                pendentes.append({"linha": i + 2, "id": row[0], "produto": row[1],
                                  "tipo": row[2], "idioma": row[3], "pais": row[4],
                                  "perfil_voz": row[5], "prompt_extra": row[6]})
        return pendentes
    except Exception as e:
        logger.error(f"Sheets leitura erro: {e}")
        return []

def sheets_atualizar(linha: int, status: str, video_url: str = "", audio_url: str = ""):
    """Atualiza status e URLs de uma linha"""
    try:
        sheet = _sheets_service()
        sheet.values().update(
            spreadsheetId=SHEET_ID,
            range=f"H{linha}:J{linha}",
            valueInputOption="RAW",
            body={"values": [[status, video_url, audio_url]]}
        ).execute()
    except Exception as e:
        logger.error(f"Sheets update erro: {e}")

def sheets_adicionar(produto: str, tipo: str, idioma: str, pais: str,
                     perfil_voz: str = "young_female", prompt_extra: str = "",
                     status: str = "pendente") -> int:
    """Adiciona nova linha e retorna o número dela"""
    try:
        sheet = _sheets_service()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range="A:A").execute()
        proxima = len(result.get("values", [])) + 1
        nova_id = str(proxima - 1)
        sheet.values().update(
            spreadsheetId=SHEET_ID,
            range=f"A{proxima}",
            valueInputOption="RAW",
            body={"values": [[nova_id, produto, tipo, idioma, pais, perfil_voz,
                               prompt_extra, status, "", "",
                               datetime.now().strftime("%Y-%m-%d %H:%M")]]}
        ).execute()
        return proxima
    except Exception as e:
        logger.error(f"Sheets adicionar erro: {e}")
        return -1

def sheets_ler_aprovados() -> list:
    """Retorna todas as linhas com status='aprovado'"""
    try:
        sheet = _sheets_service()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range="A2:K1000").execute()
        rows = result.get("values", [])
        aprovados = []
        for i, row in enumerate(rows):
            while len(row) < 11:
                row.append("")
            if row[7].strip().lower() == "aprovado":
                aprovados.append({
                    "linha": i + 2, "id": row[0], "produto": row[1],
                    "tipo": row[2], "idioma": row[3], "pais": row[4],
                    "perfil_voz": row[5], "prompt_extra": row[6]
                })
        return aprovados
    except Exception as e:
        logger.error(f"Sheets leitura erro: {e}")
        return []

VOICE_MAP = {
    "young_female": {"id": "FGY2WhTYpPnrIDTdsKH5", "name": "Laura"},
    "adult_female": {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah"},
    "young_male":   {"id": "TX3LPaxmHKxFdv7VOQHJ", "name": "Liam"},
    "adult_male":   {"id": "JBFqnCBsd6RMkjVDRZzb", "name": "George"},
}

IDIOMAS = {
    "pt": "Português Brasileiro",
    "en": "Inglês Americano",
    "es": "Espanhol",
    "fr": "Francês",
    "de": "Alemão",
    "it": "Italiano",
}

# Mapeia message_id do Discord → linha da planilha (para aprovação por reação)
reacoes_mapa = {}  # {message_id: {"linha": int, "produto": str, "dados": dict}}

# Categorias Shein com público e voz padrão
CATEGORIAS_SHEIN = [
    {"nome": "Vestidos",           "voz": "young_female", "idioma": "pt"},
    {"nome": "Blusas e Tops",      "voz": "young_female", "idioma": "pt"},
    {"nome": "Calçados",           "voz": "young_female", "idioma": "pt"},
    {"nome": "Acessórios e Joias", "voz": "young_female", "idioma": "pt"},
    {"nome": "Maquiagem e Beleza", "voz": "adult_female", "idioma": "pt"},
    {"nome": "Bolsas",             "voz": "young_female", "idioma": "pt"},
    {"nome": "Roupas Masculinas",  "voz": "young_male",   "idioma": "pt"},
    {"nome": "Decoração e Casa",   "voz": "adult_female", "idioma": "pt"},
    {"nome": "Eletrônicos",        "voz": "young_male",   "idioma": "pt"},
    {"nome": "Artigos para Carro", "voz": "adult_male",   "idioma": "pt"},
    {"nome": "Camping e Outdoor",  "voz": "adult_male",   "idioma": "pt"},
    {"nome": "Artigos Religiosos", "voz": "adult_female", "idioma": "pt"},
    {"nome": "Roupa de Cama",      "voz": "adult_female", "idioma": "pt"},
    {"nome": "Moda Praia",         "voz": "young_female", "idioma": "pt"},
    {"nome": "Roupas Plus Size",   "voz": "adult_female", "idioma": "pt"},
]

estado = {}

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)


# ── LLM ───────────────────────────────────────────────────────────────────────

async def gemini(prompt: str, usar_busca_web: bool = False) -> str:
    """Chama o Gemini com retry e fallback de modelo."""
    modelos = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]

    for modelo in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if usar_busca_web:
            body["tools"] = [{"google_search": {}}]

        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(url, json=body) as r:
                    data = await r.json()

                    if "error" in data:
                        codigo = data["error"].get("code", 0)
                        msg_erro = data["error"].get("message", "")
                        if codigo == 429:
                            logger.warning(f"Rate limit em {modelo}, tentando proximo...")
                            await asyncio.sleep(3)
                            continue
                        raise Exception(f"Gemini erro {codigo}: {msg_erro[:200]}")

                    if "candidates" not in data or not data["candidates"]:
                        raise Exception("Resposta vazia do Gemini")

                    partes = data["candidates"][0]["content"]["parts"]
                    return "".join(p.get("text", "") for p in partes if "text" in p)

        except Exception as e:
            if "Rate limit" in str(e) or "429" in str(e):
                logger.warning(f"Rate limit em {modelo}, tentando proximo...")
                await asyncio.sleep(3)
                continue
            raise

    raise Exception("Todos os modelos Gemini atingiram o limite de cota. Aguarde alguns minutos e tente novamente.")


def parse_json(texto: str):
    texto = texto.strip()
    if "```" in texto:
        for p in texto.split("```"):
            p = p.strip().lstrip("json").strip()
            try:
                return json.loads(p)
            except:
                continue
    return json.loads(texto)


# ── ElevenLabs ────────────────────────────────────────────────────────────────

async def gerar_audio(texto: str, voice_id: str, caminho: str) -> str:
    os.makedirs("temp_audio", exist_ok=True)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
    body = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.85, "style": 0.45}
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=body, headers=headers) as r:
            if r.status != 200:
                raise Exception(f"ElevenLabs {r.status}: {await r.text()}")
            with open(caminho, "wb") as f:
                f.write(await r.read())
    return caminho


# ── Topview ───────────────────────────────────────────────────────────────────

async def topview_upload_audio(caminho_mp3: str) -> str:
    """Faz upload do MP3 para o Topview S3 e retorna o fileId"""
    async with aiohttp.ClientSession() as s:
        # Step 1: obter URL de upload
        async with s.get(
            f"{TOPVIEW_BASE}/upload/credential",
            headers=TOPVIEW_HEADERS(),
            params={"format": "mp3"}
        ) as r:
            if r.status != 200:
                raise Exception(f"Topview credential erro {r.status}: {await r.text()}")
            data = (await r.json())["result"]
            file_id   = data["fileId"]
            upload_url = data["uploadUrl"]

        # Step 2: upload para S3
        async with aiofiles.open(caminho_mp3, "rb") as f:
            audio_bytes = await f.read()

        async with s.put(
            upload_url,
            data=audio_bytes,
            headers={"Content-Type": "application/octet-stream"}
        ) as r:
            if r.status not in (200, 204):
                raise Exception(f"S3 upload erro {r.status}: {await r.text()}")

    return file_id


async def topview_get_avatar() -> str:
    """Retorna um avatarId disponivel da plataforma"""
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{TOPVIEW_BASE}/photo_avatar/template/list",
            headers=TOPVIEW_HEADERS(),
            params={"pageSize": 20, "isCustom": False, "pageNo": 1}
        ) as r:
            if r.status != 200:
                raise Exception(f"Topview avatar list erro {r.status}")
            data = (await r.json())["result"]["data"]
            if not data:
                raise Exception("Nenhum avatar disponivel")
            return data[0]["avatarId"]


async def topview_submit_video(audio_file_id: str, avatar_id: str) -> str:
    """Submete tarefa photo_avatar e retorna taskId"""
    body = {
        "avatarId": avatar_id,
        "audioFileId": audio_file_id,
        "mode": "avatar4",
        "scriptMode": "audio",
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{TOPVIEW_BASE}/photo_avatar/task/submit",
            headers=TOPVIEW_HEADERS(),
            json=body
        ) as r:
            if r.status != 200:
                raise Exception(f"Topview submit erro {r.status}: {await r.text()}")
            result = await r.json()
            if result.get("code") != "200":
                raise Exception(f"Topview submit: {result.get('message')}")
            return result["result"]["taskId"]


async def topview_aguardar_video(task_id: str, timeout: int = 300) -> str:
    """Aguarda conclusao do video e retorna a URL"""
    import time
    inicio = time.time()
    async with aiohttp.ClientSession() as s:
        while True:
            if time.time() - inicio > timeout:
                raise TimeoutError("Timeout aguardando video do Topview")

            async with s.get(
                f"{TOPVIEW_BASE}/photo_avatar/task/query",
                headers=TOPVIEW_HEADERS(),
                params={"taskId": task_id}
            ) as r:
                if r.status != 200:
                    raise Exception(f"Topview query erro {r.status}: {await r.text()}")
                data = (await r.json())["result"]
                status = data.get("status", "")

                if status == "success":
                    return data.get("finishedVideoUrl", "")
                elif status in ("failure", "failed", "error"):
                    raise Exception(f"Topview falhou: {data}")

            await asyncio.sleep(15)


async def gerar_video_completo(texto: str, voice_id: str, caminho_audio: str, status_cb=None) -> str:
    """Pipeline completo: audio → upload → video → URL"""
    if status_cb:
        await status_cb("🎙️ Gerando áudio...")
    await gerar_audio(texto, voice_id, caminho_audio)

    if status_cb:
        await status_cb("☁️ Enviando áudio para Topview...")
    file_id = await topview_upload_audio(caminho_audio)

    if status_cb:
        await status_cb("🎭 Selecionando avatar...")
    avatar_id = await topview_get_avatar()

    if status_cb:
        await status_cb("🎬 Gerando vídeo (pode levar 1-3 min)...")
    task_id = await topview_submit_video(file_id, avatar_id)

    if status_cb:
        await status_cb(f"⏳ Processando vídeo (task: `{task_id[:12]}...`)...")
    video_url = await topview_aguardar_video(task_id)

    return video_url


# ── Comandos ──────────────────────────────────────────────────────────────────

async def cmd_ajuda(message):
    await message.channel.send("""🤖 **AGENTE UGC — COMANDOS**

**🎁 OFERTA GRÁTIS (script + áudio + vídeo)**
`!gratis [produto] [idioma]`
→ Ex: `!gratis mini perfume pt`
→ Ex: `!gratis free shoes en`
→ Ex: `!gratis anillo gratis es`

Idiomas: `pt` `en` `es` `fr` `de` `it`

**🛍️ REVIEW SHEIN (script + áudio + vídeo)**
`!pesquisa [país]` → busca produtos virais na Shein (tempo real)
`!criar [número]`  → gera review UGC completo

**📋 GOOGLE SHEETS (automação)**
`!planilha` → ver tarefas pendentes
`!planilha rodar` → processar todas as pendentes
`!planilha add [produto] [tipo] [idioma] [país]`

**🚀 MODO VIRAL AUTO (tudo de uma vez)**
`!viral [país] [plataforma]`
→ Busca produtos virais + salva na planilha + gera vídeos automaticamente
→ Ex: `!viral Brasil TikTok`
→ Ex: `!viral Estados Unidos Instagram en`

**🌐 SÓ TENDÊNCIAS (sem gerar vídeo)**
`!tendencias [país]` → vê o que está viral
`!tendencias [país] tiktok` → filtra por plataforma

**🎙️ SÓ ÁUDIO (sem vídeo)**
`!audio [produto] [idioma]`
→ Ex: `!audio mini perfume pt`

**ℹ️ INFO**
`!vozes`  → lista vozes disponíveis
`!paises` → lista países disponíveis
`!ajuda`  → esta mensagem""")


async def cmd_vozes(message):
    linhas = ["🎙️ **Vozes disponíveis:**\n"]
    for perfil, v in VOICE_MAP.items():
        linhas.append(f"• `{perfil}` → {v['name']}")
    await message.channel.send("\n".join(linhas))


async def cmd_paises(message):
    paises = [
        "🇧🇷 Brasil", "🇺🇸 Estados Unidos", "🇲🇽 México",
        "🇫🇷 França", "🇩🇪 Alemanha", "🇪🇸 Espanha",
        "🇦🇷 Argentina", "🇦🇺 Austrália", "🇬🇧 Reino Unido",
        "🇨🇦 Canadá", "🇮🇹 Itália",
    ]
    await message.channel.send("🌍 **Países:**\n" + " | ".join(paises))


async def _gerar_script_gratis(produto: str, idioma_nome: str) -> dict:
    prompt = f"""Você é especialista em scripts UGC para TikTok e Meta Ads.
Crie um script no estilo "produto grátis" para o produto abaixo.

Produto: {produto}
Idioma: {idioma_nome}

Estilo: natural, como pessoa real gravando no celular. Urgência. CTA claro.
Duração: 15-25 segundos de fala.

Responda APENAS com JSON válido:
{{
  "script": "script completo para áudio",
  "gancho": "primeira frase de abertura",
  "cta": "chamada para ação final",
  "duracao_estimada": 20
}}"""
    return parse_json(await gemini(prompt))


async def cmd_gratis(message, args: list, gerar_vid: bool = True):
    if len(args) < 2:
        await message.channel.send("❌ Use: `!gratis [produto] [idioma]`\nEx: `!gratis mini perfume pt`")
        return

    perfil_voz = "young_female"
    if args[-1] in VOICE_MAP:
        perfil_voz = args.pop()

    idioma_codigo = "pt"
    if args[-1].lower() in IDIOMAS:
        idioma_codigo = args.pop().lower()

    produto    = " ".join(args)
    idioma_nome = IDIOMAS[idioma_codigo]
    voz        = VOICE_MAP[perfil_voz]

    msg = await message.channel.send(f"⚙️ Iniciando pipeline UGC para **{produto}**...")

    async def atualizar(texto):
        await msg.edit(content=texto)

    try:
        await atualizar("📝 Gerando script...")
        dados = await _gerar_script_gratis(produto, idioma_nome)

        nome_audio = f"temp_audio/gratis_{produto[:20].replace(' ','_')}_{idioma_codigo}.mp3"

        if gerar_vid:
            video_url = await gerar_video_completo(
                dados["script"], voz["id"], nome_audio, atualizar
            )
        else:
            await atualizar("🎙️ Gerando áudio...")
            await gerar_audio(dados["script"], voz["id"], nome_audio)
            video_url = None

        resultado = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎁 **OFERTA GRÁTIS — UGC PRONTO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 **Produto:** {produto}
🗣️ **Idioma:** {idioma_nome} | 🎙️ **Voz:** {voz['name']}
⏱️ **Duração:** ~{dados.get('duracao_estimada','?')}s

🎯 **Gancho:** {dados.get('gancho','')}

📢 **Script:**
{dados.get('script','')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        if video_url:
            resultado += f"\n🎬 **Vídeo gerado:**\n{video_url}"
        else:
            resultado += "\n🔊 Áudio gerado (vídeo desativado)"

        resultado += "\n\nReaja: 👍 APROVAR | 👎 REJEITAR | 🔄 REFAZER"
        await msg.edit(content=resultado)

        # Enviar arquivo de audio
        if os.path.exists(nome_audio):
            await message.channel.send(
                content=f"🔊 **Áudio:** {produto} ({idioma_nome})",
                file=discord.File(nome_audio, filename=f"ugc_{produto[:25].replace(' ','_')}.mp3")
            )

    except Exception as e:
        logger.error(f"Erro cmd_gratis: {e}")
        await msg.edit(content=f"❌ Erro: `{str(e)[:400]}`")


async def cmd_audio(message, args: list):
    """Gera só o audio, sem video"""
    await cmd_gratis(message, args, gerar_vid=False)


async def cmd_pesquisa(message, pais: str):
    msg = await message.channel.send(f"🔍 Buscando produtos virais na Shein — **{pais}** (pesquisa em tempo real)...")
    prompt = f"""Pesquise agora na internet os produtos que estão mais virais e em alta na Shein em {pais} em 2025.
Busque no Google, TikTok trending e redes sociais deste país.
Foque em produtos que estão gerando muitas vendas e engajamento.

Retorne APENAS um JSON válido com os 5 produtos mais relevantes (sem markdown):
[{{"numero":1,"produto":"nome exato do produto","categoria":"categoria","preco_estimado":"preço em moeda local","por_que_viral":"razão real baseada em tendência atual","publico_alvo":"perfil de quem compra"}}]"""

    try:
        resposta = await gemini(prompt, usar_busca_web=True)
        produtos = parse_json(resposta)
        estado[message.channel.id] = {"pais": pais, "produtos": produtos}
        linhas = [f"✅ **Shein viral — {pais}** *(busca em tempo real)*\n"]
        for p in produtos:
            linhas.append(
                f"**{p['numero']}. {p['produto']}**\n"
                f"   📦 {p['categoria']} | 💰 {p['preco_estimado']}\n"
                f"   📈 {p['por_que_viral']} | 👥 {p['publico_alvo']}\n"
            )
        linhas.append("Digite `!criar [número]` para gerar o UGC completo.")
        await msg.edit(content="\n".join(linhas))
    except Exception as e:
        logger.error(f"Erro pesquisa: {e}")
        await msg.edit(content=f"❌ Erro: `{str(e)[:200]}`")


async def cmd_tendencias(message, args: list):
    """Busca tendencias virais em qualquer plataforma/pais/nicho"""
    if not args:
        await message.channel.send("❌ Use: `!tendencias [país] [plataforma opcional]`\nEx: `!tendencias Brasil TikTok`\nEx: `!tendencias EUA Instagram`")
        return

    plataforma = ""
    if len(args) > 1 and args[-1].lower() in ["tiktok", "instagram", "shein", "google", "youtube"]:
        plataforma = args.pop()
    pais = " ".join(args)
    plat_texto = f"no {plataforma}" if plataforma else "no TikTok, Instagram e Google Shopping"

    msg = await message.channel.send(f"🌐 Buscando tendências {plat_texto} — **{pais}** (tempo real)...")

    prompt = f"""Pesquise agora na internet quais produtos, nichos e conteúdos estão mais virais e em tendência {plat_texto} em {pais} em 2025.
Busque dados reais e atuais.

Retorne APENAS JSON válido (sem markdown):
{{
  "pais": "{pais}",
  "plataforma": "{plataforma or 'Geral'}",
  "tendencias": [
    {{
      "numero": 1,
      "produto_ou_nicho": "nome",
      "categoria": "categoria",
      "por_que_viral": "razão real e atual",
      "publico_alvo": "perfil",
      "oportunidade_ugc": "como criar um UGC para isso"
    }}
  ]
}}"""

    try:
        resposta = await gemini(prompt, usar_busca_web=True)
        dados = parse_json(resposta)
        tendencias = dados.get("tendencias", [])

        # Salvar como produtos para poder usar !criar depois
        produtos = [{"numero": t["numero"], "produto": t["produto_ou_nicho"], "categoria": t["categoria"],
                     "preco_estimado": "variável", "por_que_viral": t["por_que_viral"],
                     "publico_alvo": t["publico_alvo"]} for t in tendencias]
        estado[message.channel.id] = {"pais": pais, "produtos": produtos}

        linhas = [f"🌐 **Tendências — {pais}** | {dados.get('plataforma','Geral')} *(tempo real)*\n"]
        for t in tendencias:
            linhas.append(
                f"**{t['numero']}. {t['produto_ou_nicho']}**\n"
                f"   📦 {t['categoria']}\n"
                f"   📈 {t['por_que_viral']}\n"
                f"   👥 {t['publico_alvo']}\n"
                f"   💡 *UGC:* {t['oportunidade_ugc']}\n"
            )
        linhas.append("Use `!criar [número]` para gerar o vídeo UGC.")
        await msg.edit(content="\n".join(linhas))

    except Exception as e:
        logger.error(f"Erro tendencias: {e}")
        await msg.edit(content=f"❌ Erro: `{str(e)[:300]}`")


async def cmd_criar(message, numero: int):
    canal_id = message.channel.id
    if canal_id not in estado:
        await message.channel.send("❌ Faça `!pesquisa [país]` primeiro.")
        return

    produtos = estado[canal_id]["produtos"]
    pais     = estado[canal_id]["pais"]
    produto  = next((p for p in produtos if p["numero"] == numero), None)

    if not produto:
        await message.channel.send(f"❌ Número inválido. Use 1 a {len(produtos)}.")
        return

    msg = await message.channel.send(f"⚙️ Gerando UGC completo — **{produto['produto']}**...")

    async def atualizar(texto):
        await msg.edit(content=texto)

    try:
        # Persona
        await atualizar("👤 Criando persona...")
        persona_prompt = f"""Persona UGC para review Shein.
Produto: {produto['produto']} | Público: {produto['publico_alvo']} | País: {pais}
JSON: {{"nome":"Ana","idade":24,"genero":"feminino","perfil_voz":"young_female","estilo":"animada","bio_curta":"frase"}}
perfil_voz: young_female, adult_female, young_male ou adult_male"""
        persona = parse_json(await gemini(persona_prompt))
        voz = VOICE_MAP.get(persona.get("perfil_voz", "young_female"), VOICE_MAP["young_female"])

        # Script
        await atualizar("📝 Gerando roteiro...")
        idiomas_pais = {"Brasil":"pt","Estados Unidos":"en","México":"es","França":"fr","Alemanha":"de","Espanha":"es","Argentina":"es","Austrália":"en","Reino Unido":"en","Canadá":"en","Itália":"it"}
        idioma_nome = IDIOMAS.get(idiomas_pais.get(pais, "pt"), "Português Brasileiro")

        script_prompt = f"""Você é {persona['nome']}, {persona['bio_curta']}. Estilo: {persona['estilo']}. Idioma: {idioma_nome}.
Review UGC para TikTok/Reels do produto Shein. Tom natural, como alguém gravando no celular.
Produto: {produto['produto']} | Preço: {produto['preco_estimado']} | Viral: {produto['por_que_viral']}
JSON: {{"gancho":"3s abertura","corpo":"review 3-4 frases","cta":"acao","roteiro_completo":"texto completo","duracao_estimada":30}}"""

        roteiro = parse_json(await gemini(script_prompt))
        nome_audio = f"temp_audio/review_{pais.lower().replace(' ','_')}_{numero}.mp3"

        # Video completo
        video_url = await gerar_video_completo(
            roteiro["roteiro_completo"], voz["id"], nome_audio, atualizar
        )

        resultado = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛍️ **REVIEW UGC SHEIN — PRONTO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 {pais} | 📦 {produto['produto']} | 💰 {produto['preco_estimado']}
👤 {persona['nome']}, {persona['idade']} anos | 🎙️ {voz['name']} | ⏱️ ~{roteiro.get('duracao_estimada','?')}s

🎯 **Gancho:** {roteiro.get('gancho','')}
📝 {roteiro.get('corpo','')}
📢 {roteiro.get('cta','')}

🎬 **Vídeo:**
{video_url}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reaja: 👍 APROVAR | 👎 REJEITAR | 🔄 REFAZER"""

        await msg.edit(content=resultado)

        if os.path.exists(nome_audio):
            await message.channel.send(
                content="🔊 Áudio do review:",
                file=discord.File(nome_audio, filename=f"review_{produto['produto'][:25].replace(' ','_')}.mp3")
            )

    except Exception as e:
        logger.error(f"Erro cmd_criar: {e}")
        await msg.edit(content=f"❌ Erro: `{str(e)[:400]}`")


async def cmd_viral(message, args: list):
    """
    Fluxo completo automatico:
    1. Busca produtos virais (tempo real)
    2. Salva na planilha
    3. Gera video de cada um
    4. Atualiza planilha com URLs
    Uso: !viral [pais] [plataforma opcional] [idioma opcional]
    Ex:  !viral Brasil TikTok
    Ex:  !viral EUA Instagram en
    """
    if not args:
        await message.channel.send(
            "❌ Use: `!viral [país] [plataforma]`\n"
            "Ex: `!viral Brasil TikTok`\n"
            "Ex: `!viral Estados Unidos Instagram`"
        )
        return

    plataformas = ["tiktok", "instagram", "shein", "google", "youtube"]
    idiomas_codigos = list(IDIOMAS.keys())

    idioma_codigo = "pt"
    plataforma = ""

    # Extrair idioma se informado no final
    if args[-1].lower() in idiomas_codigos:
        idioma_codigo = args.pop().lower()

    # Extrair plataforma se informada
    if args and args[-1].lower() in plataformas:
        plataforma = args.pop()

    pais = " ".join(args)
    idioma_nome = IDIOMAS.get(idioma_codigo, "Português Brasileiro")
    plat_texto = f"no {plataforma}" if plataforma else "no TikTok e Instagram"

    msg = await message.channel.send(
        f"🌐 **MODO VIRAL AUTO** — {pais} {plat_texto}\n"
        f"Etapa 1/3: Buscando produtos virais em tempo real..."
    )

    try:
        # 1. Buscar produtos virais
        prompt = f"""Pesquise agora na internet os 3 produtos mais virais {plat_texto} em {pais} em 2025.
Foque em produtos de moda, beleza, casa ou acessórios que estão gerando muita venda e engajamento.

Retorne APENAS JSON válido (sem markdown):
[
  {{
    "produto": "nome do produto",
    "categoria": "categoria",
    "preco_estimado": "preço em moeda local",
    "por_que_viral": "razão real e atual",
    "publico_alvo": "perfil de quem compra"
  }}
]"""

        resposta = await gemini(prompt, usar_busca_web=True)
        produtos = parse_json(resposta)

        nomes = [p["produto"] for p in produtos]
        await msg.edit(content=(
            f"🌐 **MODO VIRAL AUTO** — {pais}\n"
            f"✅ Etapa 1/3: {len(produtos)} produtos encontrados: {', '.join(nomes)}\n"
            f"⚙️ Etapa 2/3: Salvando na planilha e gerando vídeos..."
        ))

        # 2. Salvar na planilha e processar cada produto
        resultados = []
        for i, produto in enumerate(produtos, 1):
            nome = produto["produto"]

            # Salvar na planilha
            linha = sheets_adicionar(
                produto=nome,
                tipo="gratis",
                idioma=idioma_codigo,
                pais=pais,
                perfil_voz="young_female",
                prompt_extra=produto.get("por_que_viral", "")
            )

            await msg.edit(content=(
                f"🌐 **MODO VIRAL AUTO** — {pais}\n"
                f"✅ {len(produtos)} produtos | 📋 Salvos na planilha\n"
                f"🎬 Gerando vídeo {i}/{len(produtos)}: **{nome}**..."
            ))

            # Gerar script UGC para este produto
            script_prompt = f"""Crie um script UGC curto e natural de oferta para o produto abaixo.
Produto: {nome} | Categoria: {produto['categoria']} | Por que viral: {produto['por_que_viral']}
Idioma: {idioma_nome} | Tom: natural, entusiasmado, como pessoa real no TikTok
Duração: 15-20 segundos

Responda APENAS JSON:
{{"script": "script completo para áudio", "duracao_estimada": 18}}"""

            try:
                dados_script = parse_json(await gemini(script_prompt))
                script_texto = dados_script.get("script", nome)

                nome_audio = f"temp_audio/viral_{pais[:8].replace(' ','_')}_{i}.mp3"
                await gerar_audio(script_texto, VOICE_MAP["young_female"]["id"], nome_audio)

                file_id = await topview_upload_audio(nome_audio)
                avatar_id = await topview_get_avatar()
                task_id = await topview_submit_video(file_id, avatar_id)
                video_url = await topview_aguardar_video(task_id)

                sheets_atualizar(linha, "pronto", video_url, nome_audio)
                resultados.append({"produto": nome, "linha": linha, "video_url": video_url, "script": script_texto})

            except Exception as e:
                logger.error(f"Erro gerando video para {nome}: {e}")
                sheets_atualizar(linha, "erro")
                resultados.append({"produto": nome, "linha": linha, "video_url": "", "erro": str(e)})

        # 3. Resumo final
        resumo = [f"🎉 **MODO VIRAL AUTO — CONCLUÍDO**\n🌍 {pais} | {plat_texto}\n"]
        for r in resultados:
            if r.get("video_url"):
                resumo.append(f"✅ **{r['produto']}** (L{r['linha']})\n🎬 {r['video_url']}\n")
            else:
                resumo.append(f"❌ **{r['produto']}** — erro: {r.get('erro','')[:100]}\n")
        resumo.append("📋 Tudo registrado na planilha Google Sheets.")

        await msg.edit(content="\n".join(resumo))

        # Enviar audios
        for r in resultados:
            audio_path = f"temp_audio/viral_{pais[:8].replace(' ','_')}_{resultados.index(r)+1}.mp3"
            if os.path.exists(audio_path):
                await message.channel.send(
                    content=f"🔊 {r['produto']}",
                    file=discord.File(audio_path, filename=f"viral_{r['produto'][:20].replace(' ','_')}.mp3")
                )

    except Exception as e:
        logger.error(f"Erro cmd_viral: {e}")
        await msg.edit(content=f"❌ Erro: `{str(e)[:400]}`")


# ── Events ─────────────────────────────────────────────────────────────────────

async def cmd_descobrir(message, args: list):
    """
    Pesquisa produtos virais Shein + TikTok e preenche a planilha.
    UMA unica chamada ao Gemini com todas as categorias (evita rate limit).
    Uso: !descobrir [pais]
    Ex:  !descobrir Brasil
    Ex:  !descobrir Estados Unidos
    """
    if not args:
        await message.channel.send(
            "❌ Use: `!descobrir [país]`\n"
            "Ex: `!descobrir Brasil`\n"
            "Ex: `!descobrir Estados Unidos`"
        )
        return

    pais = " ".join(args)  # Suporta paises com espacos: "Estados Unidos"

    # Expandir siglas para nome completo
    siglas = {
        "br": "Brasil", "us": "Estados Unidos", "usa": "Estados Unidos",
        "eua": "Estados Unidos", "mx": "México", "ar": "Argentina",
        "es": "Espanha", "fr": "França", "de": "Alemanha",
        "it": "Itália", "uk": "Reino Unido", "au": "Austrália",
        "ca": "Canadá", "pt": "Portugal", "co": "Colômbia",
        "cl": "Chile", "pe": "Peru",
    }
    if pais.lower() in siglas:
        pais = siglas[pais.lower()]

    idioma_por_pais = {
        "estados unidos": "en", "reino unido": "en", "austrália": "en", "canadá": "en",
        "brasil": "pt", "portugal": "pt",
        "méxico": "es", "argentina": "es", "espanha": "es", "colômbia": "es",
        "chile": "es", "peru": "es",
        "frança": "fr",
        "alemanha": "de",
        "itália": "it",
    }
    idioma = idioma_por_pais.get(pais.lower(), "pt")
    idioma_nome = IDIOMAS.get(idioma, "Português Brasileiro")

    msg = await message.channel.send(
        f"🔍 **DESCOBRIR PRODUTOS VIRAIS**\n"
        f"🌍 **{pais}** | 🗣️ {idioma_nome}\n"
        f"Pesquisando Shein + TikTok em tempo real..."
    )

    # UMA unica chamada com todas as categorias — evita rate limit
    categorias_lista = ", ".join([c["nome"] for c in CATEGORIAS_SHEIN])
    prompt = f"""Pesquise agora os produtos mais virais da Shein em {pais} em 2025.
Busque no Google, TikTok e Instagram tendências reais e atuais.
Para cada categoria abaixo, encontre 1 produto viral específico.

Categorias: {categorias_lista}

Retorne APENAS JSON válido (sem markdown), lista com até 8 produtos:
[
  {{
    "produto": "nome exato e específico do produto",
    "categoria": "nome da categoria",
    "preco_estimado": "preço em moeda local de {pais}",
    "por_que_viral": "razão real (1 frase)",
    "publico_alvo": "quem compra",
    "perfil_voz": "young_female, adult_female, young_male ou adult_male"
  }}
]"""

    try:
        resposta = await gemini(prompt, usar_busca_web=True)
        todos_produtos = parse_json(resposta)
        for p in todos_produtos:
            p["idioma"] = idioma
    except Exception as e:
        await msg.edit(content=f"❌ Erro na pesquisa: `{str(e)[:200]}`\nTente novamente em 1-2 minutos.")
        return

    if not todos_produtos:
        await msg.edit(content="❌ Nenhum produto encontrado. Tente novamente.")
        return

    await msg.edit(content=(
        f"✅ **{len(todos_produtos)} produtos encontrados** — {pais}\n"
        f"Salvando na planilha e postando para aprovação..."
    ))

    # Criar aba especifica para o pais na planilha (se nao existir)
    _garantir_aba_pais(pais)

    await message.channel.send(
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 **APROVAÇÃO — {pais.upper()}** | {idioma_nome}\n"
        f"Reaja ✅ para aprovar ou ❌ para rejeitar.\n"
        f"Ou mude o status na planilha para `aprovado`.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    for p in todos_produtos:
        voz_cat = next((c["voz"] for c in CATEGORIAS_SHEIN if c["nome"] == p.get("categoria")), "young_female")
        p["perfil_voz"] = p.get("perfil_voz", voz_cat)

        linha = sheets_adicionar(
            produto=p["produto"],
            tipo="review_shein",
            idioma=idioma,
            pais=pais,
            perfil_voz=p["perfil_voz"],
            prompt_extra=p.get("por_que_viral", ""),
            status="sugerido"
        )

        texto = (
            f"**{p['produto']}**\n"
            f"📦 {p['categoria']} | 💰 {p.get('preco_estimado','N/A')}\n"
            f"📈 {p.get('por_que_viral','')}\n"
            f"👥 {p.get('publico_alvo','')} | 🎙️ {p['perfil_voz']}\n"
            f"_Linha {linha} — {pais}_"
        )
        msg_produto = await message.channel.send(texto)
        await msg_produto.add_reaction("✅")
        await msg_produto.add_reaction("❌")

        reacoes_mapa[msg_produto.id] = {
            "linha": linha,
            "produto": p["produto"],
            "pais": pais,
            "idioma": idioma,
            "perfil_voz": p["perfil_voz"],
            "por_que_viral": p.get("por_que_viral", ""),
        }
        await asyncio.sleep(0.5)

    await message.channel.send(
        f"✅ **{len(todos_produtos)} produtos** salvos na planilha.\n"
        f"Reaja acima ou aprove na planilha. Depois use `!processar`."
    )


def _garantir_aba_pais(pais: str):
    """Cria uma aba na planilha com o nome do pais, se nao existir"""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_service_account_file(
            CREDS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)

        # Verificar abas existentes
        meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        abas = [s["properties"]["title"] for s in meta["sheets"]]

        if pais not in abas:
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={"requests": [{"addSheet": {"properties": {"title": pais}}}]}
            ).execute()
            # Adicionar cabecalho na nova aba
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"{pais}!A1",
                valueInputOption="RAW",
                body={"values": [["ID","produto","tipo","idioma","pais","perfil_voz","prompt_extra","status","video_url","audio_url","criado_em"]]}
            ).execute()
            logger.info(f"Aba '{pais}' criada na planilha.")
    except Exception as e:
        logger.warning(f"Nao foi possivel criar aba '{pais}': {e}")


async def cmd_processar(message):
    """Lê aprovados na planilha e gera videos de todos"""
    aprovados = sheets_ler_aprovados()
    if not aprovados:
        await message.channel.send(
            "📋 Nenhum produto com status `aprovado` na planilha.\n"
            "Use `!descobrir [país]` para sugerir produtos e aprove com ✅ ou na planilha."
        )
        return

    await message.channel.send(
        f"▶️ **Processando {len(aprovados)} produto(s) aprovado(s)...**\n"
        f"Isso pode levar alguns minutos. Você será notificado a cada vídeo pronto."
    )

    for tarefa in aprovados:
        await _processar_tarefa_planilha(message.channel, tarefa)
        await asyncio.sleep(2)

    await message.channel.send(f"🎉 **Todos os {len(aprovados)} vídeos foram processados!** Confira a planilha para as URLs.")


async def cmd_planilha(message, args: list):
    """Gerencia a planilha de campanhas"""
    if not args:
        # Mostrar pendentes
        pendentes = sheets_ler_pendentes()
        if not pendentes:
            await message.channel.send(
                "📋 **Planilha** — nenhuma tarefa pendente.\n\n"
                "Para adicionar via Discord:\n"
                "`!planilha add [produto] [tipo] [idioma] [país]`\n"
                "Ex: `!planilha add \"mini perfume\" gratis pt Brasil`\n\n"
                "Ou adicione diretamente na planilha com status `pendente` e use `!planilha rodar`"
            )
        else:
            linhas = [f"📋 **{len(pendentes)} tarefa(s) pendente(s) na planilha:**\n"]
            for p in pendentes:
                linhas.append(f"• Linha {p['linha']}: **{p['produto']}** | {p['tipo']} | {p['idioma']} | {p['pais']}")
            linhas.append("\nUse `!planilha rodar` para processar todas.")
            await message.channel.send("\n".join(linhas))

    elif args[0].lower() == "rodar":
        pendentes = sheets_ler_pendentes()
        if not pendentes:
            await message.channel.send("📋 Nenhuma tarefa pendente na planilha.")
            return
        await message.channel.send(f"▶️ Processando **{len(pendentes)}** tarefa(s) da planilha...")
        for tarefa in pendentes:
            await _processar_tarefa_planilha(message.channel, tarefa)

    elif args[0].lower() == "add" and len(args) >= 5:
        produto    = args[1].strip('"')
        tipo       = args[2]
        idioma     = args[3]
        pais       = " ".join(args[4:])
        linha = sheets_adicionar(produto, tipo, idioma, pais)
        if linha > 0:
            await message.channel.send(f"✅ Adicionado na planilha (linha {linha}): **{produto}** | {tipo} | {idioma} | {pais}\nUse `!planilha rodar` para processar.")
        else:
            await message.channel.send("❌ Erro ao adicionar na planilha.")
    else:
        await message.channel.send(
            "📋 **Comandos da planilha:**\n"
            "`!planilha` — ver pendentes\n"
            "`!planilha rodar` — processar todas as pendentes\n"
            "`!planilha add [produto] [tipo] [idioma] [país]`\n"
            "Tipos: `gratis` ou `review_shein`\n"
            "Idiomas: `pt` `en` `es` `fr`"
        )


async def _processar_tarefa_planilha(canal, tarefa: dict):
    """Processa uma tarefa da planilha e atualiza o status"""
    produto    = tarefa["produto"]
    tipo       = tarefa["tipo"]
    idioma     = tarefa["idioma"]
    perfil_voz = tarefa.get("perfil_voz", "young_female")
    linha      = tarefa["linha"]
    voz        = VOICE_MAP.get(perfil_voz, VOICE_MAP["young_female"])
    idioma_nome = IDIOMAS.get(idioma, "Português Brasileiro")

    msg = await canal.send(f"⚙️ **[Planilha L{linha}]** Processando: **{produto}**...")
    sheets_atualizar(linha, "processando")

    async def atualizar(texto):
        await msg.edit(content=f"[L{linha}] {texto}")

    try:
        dados = await _gerar_script_gratis(produto, idioma_nome)
        nome_audio = f"temp_audio/sheet_{linha}_{produto[:15].replace(' ','_')}.mp3"
        video_url = await gerar_video_completo(dados["script"], voz["id"], nome_audio, atualizar)

        sheets_atualizar(linha, "pronto", video_url, nome_audio)

        await msg.edit(content=(
            f"✅ **[Planilha L{linha}] PRONTO** — {produto}\n"
            f"🎙️ Voz: {voz['name']} | ⏱️ ~{dados.get('duracao_estimada','?')}s\n\n"
            f"📢 **Script:** {dados.get('script','')[:300]}\n\n"
            f"🎬 **Vídeo:** {video_url}"
        ))

        if os.path.exists(nome_audio):
            await canal.send(
                content=f"🔊 Áudio L{linha}: {produto}",
                file=discord.File(nome_audio, filename=f"ugc_L{linha}_{produto[:20]}.mp3")
            )

    except Exception as e:
        sheets_atualizar(linha, "erro")
        await msg.edit(content=f"❌ **[Planilha L{linha}] Erro:** `{str(e)[:300]}`")


@client.event
async def on_ready():
    logger.info(f"Bot online: {client.user}")
    canal = client.get_channel(CHANNEL_ID)
    if canal:
        await canal.send(
            "🤖 **Agente UGC online!** Pipeline completo + Google Sheets ativado.\n\n"
            "**Início rápido:**\n"
            "• `!gratis mini perfume pt` — gera script + áudio + **vídeo**\n"
            "• `!audio mini perfume pt` — só áudio\n"
            "• `!pesquisa Brasil` — produtos virais Shein\n"
            "• `!tendencias Brasil TikTok` — tendências em tempo real\n"
            "• `!planilha` — gerenciar campanhas via Google Sheets\n\n"
            "Digite `!ajuda` para todos os comandos."
        )


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != CHANNEL_ID:
        return

    c = message.content.strip()

    if c.lower() == "!ajuda":
        await cmd_ajuda(message)
    elif c.lower() == "!vozes":
        await cmd_vozes(message)
    elif c.lower() == "!paises":
        await cmd_paises(message)
    elif c.lower().startswith("!gratis "):
        await cmd_gratis(message, c[8:].strip().split())
    elif c.lower().startswith("!audio "):
        await cmd_audio(message, c[7:].strip().split())
    elif c.lower().startswith("!pesquisa "):
        await cmd_pesquisa(message, c[10:].strip())
    elif c.lower().startswith("!tendencias "):
        await cmd_tendencias(message, c[12:].strip().split())
    elif c.lower() == "!tendencias":
        await message.channel.send("❌ Use: `!tendencias [país]`\nEx: `!tendencias Brasil`")
    elif c.lower().startswith("!criar "):
        try:
            await cmd_criar(message, int(c[7:].strip()))
        except ValueError:
            await message.channel.send("❌ Use: `!criar 1`")
    elif c.lower().startswith("!planilha"):
        args = c[9:].strip().split()
        await cmd_planilha(message, args)
    elif c.lower().startswith("!viral "):
        await cmd_viral(message, c[7:].strip().split())
    elif c.lower() == "!viral":
        await message.channel.send("❌ Use: `!viral [país]`\nEx: `!viral Brasil TikTok`")
    elif c.lower().startswith("!descobrir "):
        await cmd_descobrir(message, c[11:].strip().split())
    elif c.lower() in ("!descobrir", "!descobrir "):
        await message.channel.send(
            "❌ Use: `!descobrir [país ou sigla]`\n"
            "Ex: `!descobrir br` | `!descobrir us` | `!descobrir mx`\n"
            "Siglas: `br` `us` `mx` `ar` `es` `fr` `de` `it` `uk` `au` `ca` `pt` `co` `cl`"
        )
    elif c.lower() == "!processar":
        await cmd_processar(message)


@client.event
async def on_reaction_add(reaction, user):
    """Detecta reacao ✅ ou ❌ nas mensagens de aprovacao de produto"""
    if user.bot:
        return
    if reaction.message.channel.id != CHANNEL_ID:
        return
    if reaction.message.id not in reacoes_mapa:
        return

    dados = reacoes_mapa[reaction.message.id]
    emoji = str(reaction.emoji)

    if emoji == "✅":
        sheets_atualizar(dados["linha"], "aprovado")
        await reaction.message.channel.send(
            f"✅ **{dados['produto']}** aprovado! (L{dados['linha']})\n"
            f"Use `!processar` quando quiser gerar todos os vídeos aprovados."
        )
        reacoes_mapa.pop(reaction.message.id, None)

    elif emoji == "❌":
        sheets_atualizar(dados["linha"], "rejeitado")
        await reaction.message.channel.send(
            f"❌ **{dados['produto']}** rejeitado. (L{dados['linha']})"
        )
        reacoes_mapa.pop(reaction.message.id, None)


# ── Start ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.add("logs/bot_{time}.log", rotation="10 MB", level="INFO")
    logger.info("Iniciando bot...")
    client.run(DISCORD_TOKEN)
