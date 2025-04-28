import yt_dlp
import logging
import os
from utils import formatar_tamanho, limpar_nome_arquivo

class VideoDownloader:
    def __init__(self):
        self.taxa_download = "0 KB/s"
        self.tamanho_total = "0 MB"
        self.baixado_atual = "0 MB"
        self.titulo_video = None

    def baixar_video(self, url, diretorio, formato, resolucao, progress_hook=None):
        ydl_opts = {
            'progress_hooks': [progress_hook] if progress_hook else [],
            'outtmpl': f'{diretorio}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'retries': 10,
            'fragment_retries': 10,
            'continuedl': True,
            'noplaylist': True,
        }

        if formato == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]
            })
        else:
            if resolucao == "Melhor disponível":
                ydl_opts['format'] = '(bestvideo[vcodec^=avc1][height<=1080][fps<=60]+bestaudio/best[height<=1080])/best'
            else:
                resolucao_num = resolucao[:-1]
                ydl_opts['format'] = f'(bestvideo[vcodec^=avc1][height<={resolucao_num}][fps<=60]+bestaudio/best[height<={resolucao_num}])/best'

            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.titulo_video = limpar_nome_arquivo(info.get('title', 'Vídeo sem título'))
                ydl.download([url])
                return True
        except Exception as e:
            logging.error(f"Erro no download: {e}")
            return False

    def atualizar_progresso(self, d):
        if d['status'] == 'downloading':
            progresso = float(d.get('_percent_str', '0%').replace('%', '')) if '_percent_str' in d else \
                      (d['downloaded_bytes'] / d['total_bytes'] * 100) if 'downloaded_bytes' in d and 'total_bytes' in d else 0

            if 'speed' in d and d['speed']:
                self.taxa_download = f"{formatar_tamanho(d['speed'])}/s"

            if 'total_bytes' in d:
                self.tamanho_total = formatar_tamanho(d['total_bytes'])

            if 'downloaded_bytes' in d:
                self.baixado_atual = formatar_tamanho(d['downloaded_bytes'])

            return progresso
        return 0