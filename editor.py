import subprocess
import os
import shutil
import logging
from utils import formatar_tempo

class VideoEditor:
    def __init__(self):
        self.preview_process = None

    def obter_duracao(self, arquivo_video):
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                arquivo_video
            ]
            resultado = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(resultado.stdout.strip())
        except subprocess.CalledProcessError as e:
            logging.error(f"Erro no ffprobe: {e.stderr}")
            return 0

    def cortar_video(self, arquivo_entrada, arquivo_saida, inicio, duracao):
        try:
            cmd = [
                'ffmpeg',
                '-i', arquivo_entrada,
                '-ss', str(inicio),
                '-t', str(duracao),
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-y',
                '-loglevel', 'error',
                arquivo_saida
            ]
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Erro no ffmpeg: {e}")
            return False

    def stop_preview(self):
        if self.preview_process and self.preview_process.poll() is None:
            self.preview_process.terminate()
            self.preview_process = None

    def play_preview(self, arquivo_video, inicio, fim, janela_posicao, tamanho_janela=None):
        self.stop_preview()

        temp_dir = os.path.join(os.path.dirname(arquivo_video), "temp_preview")
        os.makedirs(temp_dir, exist_ok=True)
        temp_video = os.path.join(temp_dir, "preview.mp4")

        try:
            # Cortar o trecho selecionado
            cmd_cut = [
                'ffmpeg',
                '-ss', str(inicio),
                '-i', arquivo_video,
                '-t', str(fim - inicio),
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '30',
                '-c:a', 'aac',
                '-y',
                '-loglevel', 'error',
                temp_video
            ]
            subprocess.run(cmd_cut, check=True)

            # Definir tamanho proporcional à janela principal
            if tamanho_janela:
                largura = int(tamanho_janela[0] * 0.8)  # 80% da largura principal
                altura = int(largura * 9 / 16)  # Aspect ratio 16:9
            else:
                largura = 640
                altura = 360

            # Reproduzir o vídeo cortado
            cmd_play = [
                'ffplay',
                '-window_title', 'Pré-visualização do Corte',
                '-autoexit',
                '-noborder',
                '-left', str(janela_posicao[0] + 50),
                '-top', str(janela_posicao[1] + 50),
                '-x', str(largura),
                '-y', str(altura),
                '-loglevel', 'error',
                temp_video
            ]
            self.preview_process = subprocess.Popen(cmd_play)
            return True
        except Exception as e:
            logging.error(f"Erro na pré-visualização: {e}")
            return False

    def gerar_frame_preview(self, arquivo_video, tempo, largura, altura):
        try:
            temp_dir = os.path.join(os.path.dirname(arquivo_video), "temp_preview")
            os.makedirs(temp_dir, exist_ok=True)
            temp_image = os.path.join(temp_dir, "frame.jpg")

            cmd = [
                'ffmpeg',
                '-ss', str(tempo),
                '-i', arquivo_video,
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                '-loglevel', 'error',
                temp_image
            ]
            subprocess.run(cmd, check=True)
            return temp_image
        except Exception as e:
            logging.error(f"Erro ao gerar frame: {e}")
            return None