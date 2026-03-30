import asyncio
import os
from loguru import logger

class VideoProcessor:
    def __init__(self):
        # Verifica se o ffmpeg está instalado
        pass

    async def apply_ugc_filter(self, input_path: str, output_path: str) -> str:
        """
        Aplica filtros FFmpeg para fazer o vídeo parecer gravado com celular (UGC).
        - Adiciona leve granulação (noise)
        - Ajusta contraste e saturação para parecer câmera de iPhone
        - Garante formato 9:16 (1080x1920)
        """
        logger.info(f"Aplicando filtros UGC no vídeo: {input_path}")
        
        # Comando FFmpeg para efeito "celular/casual"
        # eq=contrast=1.05:saturation=1.1 (leve boost de cor)
        # noise=alls=2:allf=t+u (leve granulação)
        # scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920 (garante 9:16)
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.05:saturation=1.1,noise=alls=2:allf=t+u",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Erro no FFmpeg: {stderr.decode()}")
                # Se falhar, retorna o original
                return input_path
                
            logger.info(f"Filtros UGC aplicados com sucesso: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao processar vídeo com FFmpeg: {str(e)}")
            return input_path
