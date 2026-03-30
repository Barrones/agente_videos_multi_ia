# 🎬 Como o Sistema Gera Personas e Vídeos UGC (User Generated Content)

Para atingir a qualidade e o estilo dos reels de referência (autênticos, pessoas reais, alta conversão), o agente Python utiliza uma arquitetura focada em **UGC Sintético**. O objetivo é criar vídeos que pareçam gravados por uma pessoa comum com um celular, e não um anúncio super produzido ou um avatar robótico.

## 👤 1. Como as Personas (Fotos/Vídeos) São Geradas?

O sistema não usa avatares 3D genéricos. Ele utiliza a tecnologia da **HeyGen** (ou alternativas como Synthesia/Runway) focada em "Photo Avatar" ou "Video Avatar" baseados em pessoas reais.

### O Processo:
1. **Seleção do Modelo Base**: O sistema escolhe um modelo da biblioteca da API que se pareça com um criador de conteúdo comum (ex: uma mulher em um quarto, um homem no carro).
2. **Clonagem de Expressões**: A IA mapeia os movimentos faciais e labiais para o áudio gerado, garantindo que a sincronia labial (lip-sync) seja perfeita.
3. **Micro-Expressões**: O motor de IA adiciona piscadas, movimentos leves de cabeça e respirações para que a persona não pareça estática.

*Dica de Ouro*: Você também pode gravar um vídeo seu de 2 minutos (ou de um ator contratado) e treinar um avatar customizado na HeyGen. O agente Python pode usar esse seu avatar exclusivo via API para todos os vídeos!

## 🗣️ 2. Como a Voz Fica Natural?

Um vídeo UGC morre se a voz parecer o "Google Tradutor". O agente usa a **ElevenLabs** (modelo Turbo v2.5) para resolver isso.

### O Processo:
1. **Roteiro Conversacional**: A OpenAI gera o texto com marcas de hesitação (ex: "Sabe aquele problema...", "Hum, deixa eu te contar...").
2. **Clonagem/Seleção de Voz**: Usamos vozes da biblioteca da ElevenLabs categorizadas como "Conversational" ou "Narration", que têm sotaques reais e imperfeições naturais.
3. **Emoção e Pausas**: A API processa o texto inserindo respirações e pausas nos momentos certos, imitando a cadência de uma pessoa falando de improviso.

## 🎥 3. Como o Vídeo é Montado (Aparência Autêntica)?

Para não parecer um "vídeo de IA", o agente aplica técnicas de pós-processamento.

### O Processo:
1. **Geração Base**: A HeyGen junta o áudio da ElevenLabs com o avatar visual.
2. **Integração de Produto (Pic Copilot style)**: Se for um vídeo da Shein, o sistema pode usar APIs de composição de imagem para colocar o produto na mão do avatar ou em uma tela dividida (tela verde/chroma key).
3. **Filtro de Celular (FFmpeg)**: O agente Python usa a biblioteca FFmpeg para aplicar um leve "grain" (granulação), ajustar a coloração para parecer a câmera de um iPhone, e garantir o formato 9:16 (vertical).
4. **Legendas Dinâmicas**: Adiciona legendas estilo TikTok/Reels (palavra por palavra), que retêm a atenção do usuário.

## 🔄 O Fluxo Completo no Agente Python

1. **Gatilho**: O agente lê a planilha (ex: "Brasil, Shein, Maquiagem").
2. **Cérebro (OpenAI)**: Cria um roteiro de 25s focado na dor, escrito como se fosse uma amiga dando uma dica.
3. **Voz (ElevenLabs)**: Transforma o roteiro em um áudio super natural em Português BR.
4. **Visual (HeyGen)**: Pega o áudio e anima um avatar realista de uma mulher em um cenário de quarto/casa.
5. **Acabamento (FFmpeg)**: Junta tudo, ajusta a cor para parecer gravado de celular e adiciona legendas.
6. **Aprovação (Discord)**: Envia para você assistir. Se você aprovar, vai pro Drive.

## 💡 Por que isso funciona sempre?

Porque o sistema é modular. Se amanhã lançarem uma IA de vídeo melhor que a HeyGen, basta trocar o módulo `topview_client.py` pelo novo cliente, e o resto do sistema (roteiro, voz, aprovação, orquestração) continua funcionando perfeitamente. O foco está na **arquitetura de alta conversão**, não apenas na ferramenta.
