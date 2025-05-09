import tkinter as tk
import shutil
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from pathlib import Path
import threading
import yt_dlp
import logging
import webbrowser
import os
import re
import sys
import winreg
import subprocess
from datetime import timedelta
from math import ceil


# Função para obter o caminho absoluto do recurso
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funciona para desenvolvimento e para PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Configuração do sistema de logs
logging.basicConfig(
    filename='youtube_downloader.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
)

# Variáveis globais
link = None
diretorio_destino = "C:\\downVideos"  # Diretório padrão
titulo_video = None
formato_selecionado = "MP4"
resolucao_selecionada = "Melhor disponível"
taxa_download = "0 KB/s"
tamanho_total = "0 MB"
baixado_atual = "0 MB"

# Caminho para a imagem da logo
LOGO_PATH = resource_path("downVideos.png")


# Função para limpar nomes de arquivos
def limpar_nome_arquivo(nome):
    # Remove caracteres inválidos para nomes de arquivos no Windows
    nome = re.sub(r'[<>:"/\\|?*#]', '', nome)  # Remove caracteres especiais
    nome = nome.strip()  # Remove espaços no início e no final
    nome = nome.replace('\n', ' ')  # Substitui quebras de linha por espaços
    return nome


# Função para adicionar o caminho do FFmpeg ao PATH do sistema
def adicionar_ffmpeg_ao_path():
    novo_caminho = r"C:\downVideos\ffmpeg\bin"
    if novo_caminho not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + novo_caminho
        if sys.platform == "win32":
            try:
                with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as hkey:
                    with winreg.OpenKey(hkey, "Environment", 0, winreg.KEY_ALL_ACCESS) as sub_key:
                        path_value, _ = winreg.QueryValueEx(sub_key, "PATH")
                        if novo_caminho not in path_value:
                            novo_path_value = path_value + os.pathsep + novo_caminho
                            winreg.SetValueEx(sub_key, "PATH", 0, winreg.REG_EXPAND_SZ, novo_path_value)
                            logging.info(f"Caminho {novo_caminho} adicionado ao PATH do usuário.")
                            messagebox.showinfo("Sucesso",
                                                f"Caminho {novo_caminho} adicionado ao PATH. Reinicie o Windows para aplicar as alterações.")
            except Exception as e:
                logging.error(f"Erro ao adicionar o caminho ao PATH: {e}")
                messagebox.showerror("Erro", f"Erro ao adicionar o caminho ao PATH: {e}")
        else:
            logging.warning("Este script só funciona no Windows.")
            messagebox.showwarning("Aviso", "Este script só funciona no Windows.")


# Função para verificar dependências
def verificar_dependencias():
    try:
        import yt_dlp
        logging.info(f"yt-dlp versão: {yt_dlp.version.__version__}")
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            logging.info("FFmpeg encontrado e funcionando")
        except:
            logging.warning("FFmpeg não encontrado - conversões podem falhar")
    except Exception as e:
        logging.error(f"Erro nas dependências: {e}")


# Função para formatar tamanhos
def formatar_tamanho(bytes):
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.2f} KB"
    elif bytes < 1024 * 1024 * 1024:
        return f"{bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes / (1024 * 1024 * 1024):.2f} GB"


# Função para escolher o diretório de destino
def escolher_diretorio():
    global diretorio_destino
    novo_diretorio = filedialog.askdirectory(title="Escolha onde salvar o vídeo")
    if novo_diretorio:
        diretorio_destino = novo_diretorio
        label_status.config(text=f"Diretório selecionado: {diretorio_destino}")
    else:
        label_status.config(text=f"Diretório padrão: {diretorio_destino}")


# Função para verificar a plataforma do link
def verificar_plataforma(link):
    if "youtube.com" in link or "youtu.be" in link:
        return "YouTube"
    elif "instagram.com" in link:
        return "Instagram"
    elif "facebook.com" in link or "fb.watch" in link:
        return "Facebook"
    else:
        return None


# Função para obter formatos disponíveis
def obter_formatos_disponiveis(link):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(link, download=False)
            formatos = []

            for f in info.get('formats', []):
                if f.get('height'):
                    res = f"{f['height']}p"
                    if res not in formatos:
                        formatos.append(res)

            # Ordenar do maior para o menor
            formatos.sort(key=lambda x: int(x[:-1]), reverse=True)
            return ['Melhor disponível'] + formatos
    except Exception as e:
        logging.error(f"Erro ao obter formatos: {e}")
        return ['Melhor disponível']


# Função para baixar vídeo
def baixar_video(plataforma):
    global link, diretorio_destino, titulo_video, formato_selecionado, resolucao_selecionada
    global taxa_download, tamanho_total, baixado_atual

    # Resetar estatísticas
    taxa_download = "0 KB/s"
    tamanho_total = "0 MB"
    baixado_atual = "0 MB"
    label_estatisticas.config(text="Preparando download...")
    barra_progresso["value"] = 0

    link = entry_link.get()
    if not link:
        messagebox.showerror("Erro", "Por favor, insira um link.")
        return

    if not diretorio_destino:
        messagebox.showerror("Erro", "Por favor, selecione um diretório de destino.")
        return

    plataforma_link = verificar_plataforma(link)
    if plataforma_link != plataforma:
        messagebox.showerror("Erro",
                             f"O link fornecido não é da plataforma {plataforma}. Por favor, use o botão correto.")
        return

    try:
        logging.info(f"Iniciando download do vídeo: {link}")

        # Configurações para máxima qualidade
        ydl_opts = {
            'progress_hooks': [atualizar_progresso],
            'outtmpl': f'{diretorio_destino}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'retries': 10,
            'fragment_retries': 10,
            'continuedl': True,
            'noplaylist': True,
        }

        if formato_selecionado == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]
            })
        else:
            if resolucao_selecionada == "Melhor disponível":
                ydl_opts[
                    'format'] = '(bestvideo[vcodec^=avc1][height<=1080][fps<=60]+bestaudio/best[height<=1080])/best'
            else:
                resolucao = resolucao_selecionada[:-1]  # Remove o 'p'
                ydl_opts[
                    'format'] = f'(bestvideo[vcodec^=avc1][height<={resolucao}][fps<=60]+bestaudio/best[height<={resolucao}])/best'

            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            titulo_video = limpar_nome_arquivo(info.get('title', 'Vídeo sem título'))

        label_status.config(text=f"Baixando: {titulo_video}...")
        threading.Thread(target=executar_download, args=(link, ydl_opts)).start()

    except Exception as e:
        logging.error(f"Erro ao configurar o download: {e}")
        messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")


# Função para executar o download com yt-dlp
def executar_download(link, ydl_opts):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        janela.after(0, download_concluido)
    except Exception as ex:
        logging.error(f"Erro durante o download: {ex}")
        janela.after(0, lambda ex=ex: messagebox.showerror("Erro", f"Erro durante o download: {ex}"))


# Função para atualizar a barra de progresso e estatísticas
def atualizar_progresso(d):
    global taxa_download, tamanho_total, baixado_atual

    if d['status'] == 'downloading':
        # Calcular progresso percentual
        if '_percent_str' in d:
            progresso = float(d['_percent_str'].replace('%', ''))
        elif 'downloaded_bytes' in d and 'total_bytes' in d:
            progresso = (d['downloaded_bytes'] / d['total_bytes']) * 100
        else:
            progresso = 0

        # Atualizar barra de progresso
        barra_progresso["value"] = progresso

        # Atualizar estatísticas de download
        if 'speed' in d and d['speed']:
            velocidade = d['speed']
            taxa_download = formatar_tamanho(velocidade) + "/s"

        if 'total_bytes' in d and d['total_bytes']:
            tamanho_total = formatar_tamanho(d['total_bytes'])

        if 'downloaded_bytes' in d:
            baixado_atual = formatar_tamanho(d['downloaded_bytes'])

        # Atualizar labels
        label_estatisticas.config(text=f"Velocidade: {taxa_download} | Baixado: {baixado_atual} / {tamanho_total}")

        janela.update_idletasks()
        logging.info(f"Progresso: {progresso:.2f}% | Velocidade: {taxa_download}")


# Função chamada quando o download é concluído
def download_concluido():
    global link, titulo_video, taxa_download, tamanho_total, baixado_atual

    logging.info("Download concluído com sucesso!")
    messagebox.showinfo("Sucesso", "Download concluído!")
    label_status.config(text=f"Download concluído: {titulo_video}")
    barra_progresso["value"] = 100

    # Mostrar estatísticas finais
    label_estatisticas.config(text=f"Concluído! Tamanho: {tamanho_total}")

    entry_link.delete(0, tk.END)
    label_status.config(text="Pronto para novo download.")
    titulo_video = None
    botao_abrir_diretorio.config(state=tk.NORMAL)


# Função para abrir o diretório onde o vídeo foi salvo
def abrir_diretorio():
    if diretorio_destino:
        webbrowser.open(diretorio_destino)
    else:
        messagebox.showwarning("Aviso", "Nenhum diretório selecionado.")


# Função para selecionar o formato de saída
def selecionar_formato(event):
    global formato_selecionado
    formato_selecionado = combo_formatos.get()
    logging.info(f"Formato selecionado: {formato_selecionado}")
    # Desabilitar seleção de resolução se for MP3
    if formato_selecionado == "MP3":
        combo_resolucao.config(state=tk.DISABLED)
        combo_resolucao.set("Não aplicável")
    else:
        combo_resolucao.config(state=tk.NORMAL)
        combo_resolucao.set("Melhor disponível")


# Função para selecionar a resolução
def selecionar_resolucao(event):
    global resolucao_selecionada
    resolucao_selecionada = combo_resolucao.get()
    logging.info(f"Resolução selecionada: {resolucao_selecionada}")


# Função para atualizar resoluções disponíveis
def atualizar_resolucoes():
    link = entry_link.get()
    if link and verificar_plataforma(link) == "YouTube":
        formatos = obter_formatos_disponiveis(link)
        combo_resolucao['values'] = formatos
        combo_resolucao.set("Melhor disponível")
        label_status.config(text="Resoluções atualizadas!")


# Funções para corte de vídeo
def formatar_tempo(segundos):
    horas, resto = divmod(int(segundos), 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def obter_duracao_video(arquivo_video):
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
        messagebox.showerror("Erro", "Falha ao obter duração do vídeo. Verifique o FFmpeg.")
        return 0


def calcular_partes(duracao_total_seg, duracao_parte_seg):
    return ceil(duracao_total_seg / duracao_parte_seg)


def cortar_video():
    arquivo_video = filedialog.askopenfilename(
        title="Selecione o vídeo para cortar",
        filetypes=[("Vídeos", "*.mp4 *.avi *.mov *.mkv"), ("Todos os arquivos", "*.*")]
    )

    if not arquivo_video:
        return

    duracao_total = obter_duracao_video(arquivo_video)
    if duracao_total <= 0:
        return

    janela_corte = tk.Toplevel(janela)
    janela_corte.title("Configuração de Corte")
    janela_corte.geometry("450x400")

    # Centralizar a janela de corte
    centralizar_janela(janela_corte, 450, 400)

    duracao_var = tk.IntVar(value=180)
    partes_var = tk.IntVar(value=calcular_partes(duracao_total, duracao_var.get()))
    sobreposicao_var = tk.IntVar(value=5)

    def atualizar_partes(*args):
        try:
            partes = calcular_partes(duracao_total, duracao_var.get())
            partes_var.set(partes)
            label_partes.config(text=f"Número de partes: {partes}")
        except:
            pass

    duracao_var.trace_add("write", atualizar_partes)

    tk.Label(janela_corte, text="Configuração de Corte", font=('Arial', 12, 'bold')).pack(pady=10)

    frame_info = tk.Frame(janela_corte)
    frame_info.pack(pady=5)
    tk.Label(frame_info, text=f"Vídeo: {os.path.basename(arquivo_video)}").pack(anchor='w')
    tk.Label(frame_info, text=f"Duração total: {formatar_tempo(duracao_total)}").pack(anchor='w')

    tk.Label(janela_corte, text="Duração de cada parte (segundos):").pack()
    tk.Spinbox(janela_corte, from_=10, to=600, textvariable=duracao_var, width=5, command=atualizar_partes).pack()

    label_partes = tk.Label(janela_corte, text=f"Número de partes: {partes_var.get()}")
    label_partes.pack()

    tk.Label(janela_corte, text="Sobreposição entre partes (segundos):").pack()
    tk.Spinbox(janela_corte, from_=0, to=30, textvariable=sobreposicao_var, width=5).pack()

    tk.Button(janela_corte, text="Iniciar Corte",
              command=lambda: iniciar_corte(arquivo_video, partes_var.get(), duracao_var.get(), sobreposicao_var.get(),
                                            janela_corte)).pack(pady=20)


def iniciar_corte(arquivo_video, num_partes, duracao_parte, sobreposicao, janela_corte):
    janela_corte.withdraw()
    label_status.config(text="Preparando para cortar vídeo...")
    barra_progresso["value"] = 0
    janela.update_idletasks()

    threading.Thread(
        target=executar_corte,
        args=(arquivo_video, num_partes, duracao_parte, sobreposicao, janela_corte),
        daemon=True
    ).start()


def executar_corte(arquivo_video, num_partes, duracao_parte, sobreposicao, janela_corte):
    try:
        nome_base = os.path.splitext(os.path.basename(arquivo_video))[0]
        dir_cortes = os.path.join(os.path.dirname(arquivo_video), f"{nome_base}_cortes")
        os.makedirs(dir_cortes, exist_ok=True)

        for i in range(num_partes):
            tempo_inicio = i * (duracao_parte - sobreposicao)
            tempo_fim = tempo_inicio + duracao_parte

            arquivo_saida = os.path.join(dir_cortes, f"{nome_base}_parte_{i + 1}.mp4")

            cmd = [
                'ffmpeg',
                '-i', arquivo_video,
                '-ss', str(tempo_inicio),
                '-t', str(duracao_parte),
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-y',
                '-loglevel', 'error',
                arquivo_saida
            ]

            subprocess.run(cmd, check=True)

            progresso = ((i + 1) / num_partes) * 100
            barra_progresso["value"] = progresso
            label_status.config(text=f"Cortando vídeo... Parte {i + 1}/{num_partes}")
            janela.update_idletasks()

        messagebox.showinfo("Sucesso", f"Vídeo cortado em {num_partes} partes com sucesso!")
        label_status.config(text=f"Corte concluído! Salvo em: {dir_cortes}")
        barra_progresso["value"] = 100
        webbrowser.open(dir_cortes)

    except subprocess.CalledProcessError as e:
        logging.error(f"Erro no ffmpeg: {e}")
        messagebox.showerror("Erro", "Falha ao cortar vídeo. Verifique o FFmpeg.")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")
    finally:
        barra_progresso["value"] = 0
        label_status.config(text="Pronto para novos downloads")
        janela_corte.destroy()


def centralizar_janela(janela, largura, altura):
    """Centraliza uma janela na tela"""
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f'{largura}x{altura}+{x}+{y}')


def cortar_video_avancado():
    arquivo_video = filedialog.askopenfilename(
        title="Selecione o vídeo para cortar",
        filetypes=[("Vídeos", "*.mp4 *.avi *.mov *.mkv"), ("Todos os arquivos", "*.*")]
    )

    if not arquivo_video:
        return

    duracao_total = obter_duracao_video(arquivo_video)
    if duracao_total <= 0:
        return

    janela_corte = tk.Toplevel(janela)
    janela_corte.title("Corte Avançado de Vídeo")
    janela_corte.geometry("600x550")  # Aumentei a altura para 550 pixels

    # Centralizar a janela de corte avançado
    centralizar_janela(janela_corte, 600, 550)

    # Variáveis para controle do corte
    inicio_var = tk.DoubleVar(value=0)
    fim_var = tk.DoubleVar(value=duracao_total)
    preview_var = tk.BooleanVar(value=True)  # Pré-visualização ativada por padrão
    playing_var = tk.BooleanVar(value=False)  # Controle de play/pause

    # Frame principal
    frame_principal = tk.Frame(janela_corte)
    frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Canvas para visualização
    canvas_preview = tk.Canvas(frame_principal, bg='black', height=200)
    canvas_preview.pack(fill=tk.X, pady=5)

    # Frame para controles de reprodução
    frame_controles_reproducao = tk.Frame(frame_principal)
    frame_controles_reproducao.pack(fill=tk.X, pady=5)

    # Botões de controle de reprodução
    btn_play = tk.Button(
        frame_controles_reproducao,
        text="▶ Play",
        command=lambda: play_preview(),
        width=8
    )
    btn_play.pack(side=tk.LEFT, padx=5)

    btn_stop = tk.Button(
        frame_controles_reproducao,
        text="⏹ Stop",
        command=lambda: stop_preview(),
        width=8
    )
    btn_stop.pack(side=tk.LEFT, padx=5)

    # Sliders para seleção de tempo
    frame_sliders = tk.Frame(frame_principal)
    frame_sliders.pack(fill=tk.X, pady=10)

    # Slider de início
    tk.Label(frame_sliders, text="Início:").pack(anchor='w')
    slider_inicio = tk.Scale(
        frame_sliders,
        from_=0,
        to=duracao_total,
        variable=inicio_var,
        orient=tk.HORIZONTAL,
        length=550,
        resolution=1,
        command=lambda x: atualizar_preview()
    )
    slider_inicio.pack()

    # Slider de fim
    tk.Label(frame_sliders, text="Fim:").pack(anchor='w', pady=(10, 0))
    slider_fim = tk.Scale(
        frame_sliders,
        from_=0,
        to=duracao_total,
        variable=fim_var,
        orient=tk.HORIZONTAL,
        length=550,
        resolution=1,
        command=lambda x: atualizar_preview()
    )
    slider_fim.set(duracao_total)
    slider_fim.pack()

    # Labels de tempo
    frame_tempos = tk.Frame(frame_principal)
    frame_tempos.pack(fill=tk.X)

    label_tempos = tk.Label(frame_tempos, text="00:00:00 - 00:00:00")
    label_tempos.pack(side=tk.LEFT)

    label_duracao = tk.Label(frame_tempos, text=f"Duração do corte: 00:00:00")
    label_duracao.pack(side=tk.RIGHT)

    # Botões de ação na parte inferior
    frame_botoes = tk.Frame(frame_principal)
    frame_botoes.pack(fill=tk.X, pady=(20, 10))

    btn_cortar = tk.Button(
        frame_botoes,
        text="Cortar Vídeo",
        command=lambda: executar_corte_avancado(arquivo_video, inicio_var.get(), fim_var.get(), janela_corte),
        height=2,
        width=15
    )
    btn_cortar.pack(side=tk.RIGHT, padx=5)

    btn_cancelar = tk.Button(
        frame_botoes,
        text="Cancelar",
        command=janela_corte.destroy,
        height=2,
        width=15
    )
    btn_cancelar.pack(side=tk.RIGHT, padx=5)

    # Variáveis para controle de reprodução
    preview_process = None
    current_preview_time = 0

    def atualizar_tempos():
        """Atualiza os labels de tempo conforme os sliders são movidos"""
        nonlocal current_preview_time
        inicio = inicio_var.get()
        fim = fim_var.get()

        # Garantir que o início não seja maior que o fim
        if inicio > fim:
            inicio_var.set(fim)
            inicio = fim

        # Garantir que o fim não seja menor que o início
        if fim < inicio:
            fim_var.set(inicio)
            fim = inicio

        label_tempos.config(text=f"{formatar_tempo(inicio)} - {formatar_tempo(fim)}")
        duracao_corte = fim - inicio
        label_duracao.config(text=f"Duração do corte: {formatar_tempo(duracao_corte)}")

        # Resetar tempo atual da pré-visualização
        current_preview_time = inicio

    def atualizar_preview():
        """Atualiza a pré-visualização quando os sliders são movidos"""
        stop_preview()
        atualizar_tempos()
        if preview_var.get():
            gerar_preview_still()

    def gerar_preview_still():
        """Gera uma imagem estática da pré-visualização"""
        try:
            # Limpar canvas
            canvas_preview.delete("all")

            # Pegar frame do tempo atual
            frame_time = current_preview_time

            # Gerar miniatura temporária
            temp_image = os.path.join(os.path.dirname(arquivo_video), "temp_preview.jpg")

            cmd = [
                'ffmpeg',
                '-ss', str(frame_time),
                '-i', arquivo_video,
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                temp_image
            ]

            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Carregar a imagem no canvas
            img = Image.open(temp_image)
            img.thumbnail((580, 190))
            photo = ImageTk.PhotoImage(img)

            canvas_preview.image = photo  # Manter referência
            canvas_preview.create_image(0, 0, anchor='nw', image=photo)
            canvas_preview.create_text(10, 10, text=f"Pré-visualização: {formatar_tempo(frame_time)}",
                                       fill="white", anchor='nw', font=('Arial', 10, 'bold'))

            # Remover arquivo temporário
            os.remove(temp_image)

        except Exception as e:
            logging.error(f"Erro ao gerar pré-visualização: {e}")
            canvas_preview.create_text(300, 100, text="Erro ao gerar pré-visualização", fill="red", font=('Arial', 12))

    def play_preview():
        """Reproduz a seção selecionada do vídeo"""
        nonlocal preview_process, current_preview_time

        if playing_var.get():
            return

        playing_var.set(True)
        btn_play.config(state=tk.DISABLED)
        btn_stop.config(state=tk.NORMAL)

        inicio = inicio_var.get()
        fim = fim_var.get()
        current_preview_time = inicio

        # Criar diretório temporário se não existir
        temp_dir = os.path.join(os.path.dirname(arquivo_video), "temp_preview")
        os.makedirs(temp_dir, exist_ok=True)

        # Caminho para o arquivo temporário
        temp_video = os.path.join(temp_dir, "preview.mp4")

        try:
            # Primeiro cortamos o trecho selecionado para um arquivo temporário
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

            # Executar e esperar terminar
            subprocess.run(cmd_cut, check=True)

            # Verificar se o arquivo foi criado
            if not os.path.exists(temp_video):
                raise FileNotFoundError(f"Arquivo temporário não foi criado: {temp_video}")

            # Agora reproduzimos o vídeo cortado diretamente sem janela
            cmd_play = [
                'ffplay',
                '-window_title', 'Pré-visualização do Corte',
                '-autoexit',
                '-loglevel', 'error',
                '-noborder',
                '-x', '640',
                '-y', '360',
                temp_video
            ]

            preview_process = subprocess.Popen(cmd_play)

        except subprocess.CalledProcessError as e:
            logging.error(f"Erro ao cortar vídeo para pré-visualização: {e}")
            messagebox.showerror("Erro",
                                 "Falha ao preparar a pré-visualização. Verifique se o FFmpeg está instalado corretamente.")
            stop_preview()
        except FileNotFoundError as e:
            logging.error(f"Erro ao encontrar arquivo: {e}")
            messagebox.showerror("Erro", "Não foi possível criar o arquivo temporário para pré-visualização.")
            stop_preview()
        except Exception as e:
            logging.error(f"Erro inesperado ao reproduzir pré-visualização: {e}")
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")
            stop_preview()

    def stop_preview():
        """Para a reprodução da pré-visualização"""
        nonlocal preview_process
        playing_var.set(False)
        btn_play.config(state=tk.NORMAL)
        btn_stop.config(state=tk.DISABLED)

        if preview_process and preview_process.poll() is None:
            preview_process.terminate()
            preview_process = None

        # Limpar arquivos temporários
        try:
            temp_dir = os.path.join(os.path.dirname(arquivo_video), "temp_preview")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logging.error(f"Erro ao limpar arquivos temporários: {e}")

        # Mostrar frame atual ao parar
        gerar_preview_still()
# Configuração da interface gráfica
janela = tk.Tk()
janela.title("downVideos v1.6")
janela.geometry("550x750")  # Aumentado para acomodar o novo botão
janela.resizable(False, False)

# Centralizar janela principal
largura_janela = 550
altura_janela = 750
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()
x = (largura_tela // 2) - (largura_janela // 2)
y = (altura_tela // 2) - (altura_janela // 2)
janela.geometry(f'{largura_janela}x{altura_janela}+{x}+{y}')

# Ícone da janela
try:
    janela.iconbitmap(resource_path("downVideos.ico"))
except Exception as e:
    logging.warning(f"Não foi possível carregar o ícone: {e}")

# Logo do aplicativo
try:
    imagem = Image.open(resource_path("downVideos.png"))
    imagem = imagem.resize((100, 100), Image.Resampling.LANCZOS)
    imagem_tk = ImageTk.PhotoImage(imagem)
except Exception as e:
    logging.error(f"Erro ao carregar a imagem: {e}")
    imagem_tk = None

# Criar diretório padrão se não existir
if not os.path.exists(diretorio_destino):
    os.makedirs(diretorio_destino)

# COMPONENTES DA INTERFACE
# Campo de entrada para o link
label_link = tk.Label(janela, text="Cole o link do vídeo:")
label_link.pack(pady=10)

entry_link = tk.Entry(janela, width=50)
entry_link.pack(pady=5)

# Botão para atualizar resoluções
tk.Button(janela, text="Atualizar Resoluções Disponíveis", command=atualizar_resolucoes).pack(pady=5)

# Botão para escolher diretório
botao_escolher_diretorio = tk.Button(janela, text="Escolher Diretório", command=escolher_diretorio)
botao_escolher_diretorio.pack(pady=10)

# Frame para formatos
frame_formatos = tk.Frame(janela)
frame_formatos.pack(pady=5)

tk.Label(frame_formatos, text="Formato:").pack(side=tk.LEFT)
combo_formatos = ttk.Combobox(frame_formatos, values=["MP4", "MP3"], state="readonly", width=10)
combo_formatos.set("MP4")
combo_formatos.pack(side=tk.LEFT, padx=5)
combo_formatos.bind("<<ComboboxSelected>>", selecionar_formato)

tk.Label(frame_formatos, text="Resolução:").pack(side=tk.LEFT)
combo_resolucao = ttk.Combobox(frame_formatos, values=["Melhor disponível"], state="readonly", width=15)
combo_resolucao.set("Melhor disponível")
combo_resolucao.pack(side=tk.LEFT, padx=5)
combo_resolucao.bind("<<ComboboxSelected>>", selecionar_resolucao)

# Botões de plataforma
frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=10)

botao_youtube = tk.Button(frame_botoes, text="Baixar do YouTube", command=lambda: baixar_video("YouTube"))
botao_youtube.pack(side=tk.LEFT, padx=5)

botao_instagram = tk.Button(frame_botoes, text="Baixar do Instagram", command=lambda: baixar_video("Instagram"))
botao_instagram.pack(side=tk.LEFT, padx=5)

botao_facebook = tk.Button(frame_botoes, text="Baixar do Facebook", command=lambda: baixar_video("Facebook"))
botao_facebook.pack(side=tk.LEFT, padx=5)

# Botão para cortar vídeo em partes
botao_cortar = tk.Button(janela, text="Cortar Vídeo em Partes", command=cortar_video)
botao_cortar.pack(pady=5)

# Botão para corte avançado
botao_corte_avancado = tk.Button(janela, text="Corte Avançado (Selecionar Parte)", command=cortar_video_avancado)
botao_corte_avancado.pack(pady=5)

# Barra de progresso
barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=300, mode="determinate")
barra_progresso.pack(pady=10)

# Label para estatísticas de download
label_estatisticas = tk.Label(janela, text="Velocidade: 0 KB/s | Baixado: 0 MB / 0 MB", font=('Arial', 9))
label_estatisticas.pack(pady=5)

# Status
label_status = tk.Label(janela, text=f"Diretório padrão: {diretorio_destino}")
label_status.pack(pady=5)

# Botão para abrir diretório
botao_abrir_diretorio = tk.Button(janela, text="Abrir Diretório", command=abrir_diretorio, state=tk.DISABLED)
botao_abrir_diretorio.pack(pady=10)

# Logo e créditos
frame_logo_creditos = tk.Frame(janela)
frame_logo_creditos.pack(pady=10)

if imagem_tk:
    label_imagem = tk.Label(frame_logo_creditos, image=imagem_tk)
    label_imagem.image = imagem_tk
    label_imagem.pack(side=tk.TOP, pady=5)

label_creditos = tk.Label(frame_logo_creditos, text="Criado por Paulo Simplicio© - downVideos v1.6", font=("Arial", 8))
label_creditos.pack(side=tk.TOP, pady=5)

# INICIAR APLICATIVO
adicionar_ffmpeg_ao_path()
verificar_dependencias()
janela.mainloop()