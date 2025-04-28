import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import logging
import webbrowser
import os
import threading
from math import ceil
from downloader import VideoDownloader
from editor import VideoEditor
from utils import *

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.downloader = VideoDownloader()
        self.editor = VideoEditor()
        self.diretorio_destino = "C:\\downVideos"
        self.formato_selecionado = "MP4"
        self.resolucao_selecionada = "Melhor disponível"

        self.setup_logging()
        self.setup_ui()
        self.check_dependencies()

        if not os.path.exists(self.diretorio_destino):
            os.makedirs(self.diretorio_destino)

    def setup_logging(self):
        logging.basicConfig(
            filename='youtube_downloader.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8',
        )

    def check_dependencies(self):
        try:
            import yt_dlp
            try:
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except:
                logging.warning("FFmpeg não encontrado")
        except Exception as e:
            logging.error(f"Erro nas dependências: {e}")

    def setup_ui(self):
        self.root.title("downVideos v1.6")
        self.root.geometry("550x750")
        centralizar_janela(self.root, 550, 750)
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap(resource_path("downVideos.ico"))
        except Exception as e:
            logging.warning(f"Não foi possível carregar o ícone: {e}")

        # Logo
        try:
            imagem = Image.open(resource_path("downVideos.png"))
            imagem = imagem.resize((100, 100), Image.Resampling.LANCZOS)
            self.imagem_tk = ImageTk.PhotoImage(imagem)
            label_imagem = tk.Label(self.root, image=self.imagem_tk)
            label_imagem.pack(pady=5)
        except Exception as e:
            logging.error(f"Erro ao carregar a imagem: {e}")
            self.imagem_tk = None

        # Link Entry
        tk.Label(self.root, text="Cole o link do vídeo:").pack(pady=10)
        self.entry_link = tk.Entry(self.root, width=50)
        self.entry_link.pack(pady=5)

        # Update Resolutions Button
        tk.Button(self.root, text="Atualizar Resoluções Disponíveis", command=self.atualizar_resolucoes).pack(pady=5)

        # Directory Selection
        self.btn_escolher_diretorio = tk.Button(self.root, text="Escolher Diretório", command=self.escolher_diretorio)
        self.btn_escolher_diretorio.pack(pady=10)

        # Format Selection
        frame_formatos = tk.Frame(self.root)
        frame_formatos.pack(pady=5)

        tk.Label(frame_formatos, text="Formato:").pack(side=tk.LEFT)
        self.combo_formatos = ttk.Combobox(frame_formatos, values=["MP4", "MP3"], state="readonly", width=10)
        self.combo_formatos.set("MP4")
        self.combo_formatos.pack(side=tk.LEFT, padx=5)
        self.combo_formatos.bind("<<ComboboxSelected>>", self.selecionar_formato)

        tk.Label(frame_formatos, text="Resolução:").pack(side=tk.LEFT)
        self.combo_resolucao = ttk.Combobox(frame_formatos, values=["Melhor disponível"], state="readonly", width=15)
        self.combo_resolucao.set("Melhor disponível")
        self.combo_resolucao.pack(side=tk.LEFT, padx=5)
        self.combo_resolucao.bind("<<ComboboxSelected>>", self.selecionar_resolucao)

        # Platform Buttons
        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(pady=10)

        self.btn_youtube = tk.Button(frame_botoes, text="Baixar do YouTube",
                                     command=lambda: self.baixar_video("YouTube"))
        self.btn_youtube.pack(side=tk.LEFT, padx=5)

        self.btn_instagram = tk.Button(frame_botoes, text="Baixar do Instagram",
                                       command=lambda: self.baixar_video("Instagram"))
        self.btn_instagram.pack(side=tk.LEFT, padx=5)

        self.btn_facebook = tk.Button(frame_botoes, text="Baixar do Facebook",
                                      command=lambda: self.baixar_video("Facebook"))
        self.btn_facebook.pack(side=tk.LEFT, padx=5)

        # Video Editing Buttons
        self.btn_cortar = tk.Button(self.root, text="Cortar Vídeo em Partes", command=self.cortar_video)
        self.btn_cortar.pack(pady=5)

        self.btn_corte_avancado = tk.Button(self.root, text="Corte Avançado (Selecionar Parte)",
                                            command=self.cortar_video_avancado)
        self.btn_corte_avancado.pack(pady=5)

        # Progress Bar
        self.barra_progresso = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.barra_progresso.pack(pady=10)

        # Stats Label
        self.label_estatisticas = tk.Label(self.root, text="Velocidade: 0 KB/s | Baixado: 0 MB / 0 MB",
                                           font=('Arial', 9))
        self.label_estatisticas.pack(pady=5)

        # Status Label
        self.label_status = tk.Label(self.root, text=f"Diretório padrão: {self.diretorio_destino}")
        self.label_status.pack(pady=5)

        # Open Directory Button
        self.btn_abrir_diretorio = tk.Button(self.root, text="Abrir Diretório", command=self.abrir_diretorio,
                                             state=tk.DISABLED)
        self.btn_abrir_diretorio.pack(pady=10)

        # Credits
        tk.Label(self.root, text="Criado por Paulo Simplicio© - downVideos v1.6", font=("Arial", 8)).pack(pady=5)

    def escolher_diretorio(self):
        novo_diretorio = filedialog.askdirectory(title="Escolha onde salvar o vídeo")
        if novo_diretorio:
            self.diretorio_destino = novo_diretorio
            self.label_status.config(text=f"Diretório selecionado: {self.diretorio_destino}")

    def verificar_plataforma(self, link):
        if "youtube.com" in link or "youtu.be" in link:
            return "YouTube"
        elif "instagram.com" in link:
            return "Instagram"
        elif "facebook.com" in link or "fb.watch" in link:
            return "Facebook"
        return None

    def obter_formatos_disponiveis(self, link):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(link, download=False)
                formatos = [f"{f['height']}p" for f in info.get('formats', []) if f.get('height')]
                formatos = sorted(list(set(formatos)), key=lambda x: int(x[:-1]), reverse=True)
                return ['Melhor disponível'] + formatos
        except Exception as e:
            logging.error(f"Erro ao obter formatos: {e}")
            return ['Melhor disponível']

    def atualizar_resolucoes(self):
        link = self.entry_link.get()
        if link and self.verificar_plataforma(link) == "YouTube":
            formatos = self.obter_formatos_disponiveis(link)
            self.combo_resolucao['values'] = formatos
            self.combo_resolucao.set("Melhor disponível")
            self.label_status.config(text="Resoluções atualizadas!")

    def selecionar_formato(self, event):
        self.formato_selecionado = self.combo_formatos.get()
        if self.formato_selecionado == "MP3":
            self.combo_resolucao.config(state=tk.DISABLED)
            self.combo_resolucao.set("Não aplicável")
        else:
            self.combo_resolucao.config(state=tk.NORMAL)
            self.combo_resolucao.set("Melhor disponível")

    def selecionar_resolucao(self, event):
        self.resolucao_selecionada = self.combo_resolucao.get()

    def baixar_video(self, plataforma):
        link = self.entry_link.get()
        if not link:
            messagebox.showerror("Erro", "Por favor, insira um link.")
            return

        if not self.diretorio_destino:
            messagebox.showerror("Erro", "Por favor, selecione um diretório de destino.")
            return

        plataforma_link = self.verificar_plataforma(link)
        if plataforma_link != plataforma:
            messagebox.showerror("Erro", f"O link fornecido não é da plataforma {plataforma}.")
            return

        # Reset stats
        self.downloader.taxa_download = "0 KB/s"
        self.downloader.tamanho_total = "0 MB"
        self.downloader.baixado_atual = "0 MB"
        self.label_estatisticas.config(text="Preparando download...")
        self.barra_progresso["value"] = 0

        def progress_hook(d):
            progresso = self.downloader.atualizar_progresso(d)
            if progresso > 0:
                self.barra_progresso["value"] = progresso
                self.label_estatisticas.config(
                    text=f"Velocidade: {self.downloader.taxa_download} | " +
                         f"Baixado: {self.downloader.baixado_atual} / {self.downloader.tamanho_total}"
                )
                self.root.update_idletasks()

        def download_thread():
            success = self.downloader.baixar_video(
                link,
                self.diretorio_destino,
                self.formato_selecionado,
                self.resolucao_selecionada,
                progress_hook
            )

            self.root.after(0, lambda: self.download_concluido(success))

        self.label_status.config(text=f"Baixando: {link}...")
        threading.Thread(target=download_thread, daemon=True).start()

    def download_concluido(self, success):
        if success:
            messagebox.showinfo("Sucesso", "Download concluído!")
            self.label_status.config(text=f"Download concluído: {self.downloader.titulo_video}")
            self.barra_progresso["value"] = 100
            self.label_estatisticas.config(text=f"Concluído! Tamanho: {self.downloader.tamanho_total}")
            self.btn_abrir_diretorio.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Erro", "Falha ao baixar o vídeo")
            self.label_status.config(text="Erro no download")
            self.barra_progresso["value"] = 0

        self.entry_link.delete(0, tk.END)

    def abrir_diretorio(self):
        if self.diretorio_destino:
            webbrowser.open(self.diretorio_destino)

    def cortar_video(self):
        arquivo_video = filedialog.askopenfilename(
            title="Selecione o vídeo para cortar",
            filetypes=[("Vídeos", "*.mp4 *.avi *.mov *.mkv"), ("Todos os arquivos", "*.*")]
        )

        if not arquivo_video:
            return

        duracao_total = self.editor.obter_duracao(arquivo_video)
        if duracao_total <= 0:
            return

        janela_corte = tk.Toplevel(self.root)
        janela_corte.title("Configuração de Corte")
        janela_corte.geometry("450x400")
        centralizar_janela(janela_corte, 450, 400)

        duracao_var = tk.IntVar(value=180)
        partes_var = tk.IntVar(value=self.calcular_partes(duracao_total, duracao_var.get()))
        sobreposicao_var = tk.IntVar(value=5)

        def atualizar_partes(*args):
            try:
                partes = self.calcular_partes(duracao_total, duracao_var.get())
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
                  command=lambda: self.iniciar_corte(arquivo_video, partes_var.get(), duracao_var.get(),
                                                     sobreposicao_var.get(), janela_corte)).pack(pady=20)

    def calcular_partes(self, duracao_total_seg, duracao_parte_seg):
        return ceil(duracao_total_seg / duracao_parte_seg)

    def iniciar_corte(self, arquivo_video, num_partes, duracao_parte, sobreposicao, janela_corte):
        janela_corte.withdraw()
        self.label_status.config(text="Preparando para cortar vídeo...")
        self.barra_progresso["value"] = 0
        self.root.update_idletasks()

        threading.Thread(
            target=self.executar_corte,
            args=(arquivo_video, num_partes, duracao_parte, sobreposicao, janela_corte),
            daemon=True
        ).start()

    def executar_corte(self, arquivo_video, num_partes, duracao_parte, sobreposicao, janela_corte):
        try:
            nome_base = os.path.splitext(os.path.basename(arquivo_video))[0]
            dir_cortes = os.path.join(os.path.dirname(arquivo_video), f"{nome_base}_cortes")
            os.makedirs(dir_cortes, exist_ok=True)

            for i in range(num_partes):
                tempo_inicio = i * (duracao_parte - sobreposicao)
                tempo_fim = tempo_inicio + duracao_parte

                arquivo_saida = os.path.join(dir_cortes, f"{nome_base}_parte_{i + 1}.mp4")

                success = self.editor.cortar_video(
                    arquivo_video,
                    arquivo_saida,
                    tempo_inicio,
                    duracao_parte
                )

                if not success:
                    raise Exception("Falha ao cortar parte do vídeo")

                progresso = ((i + 1) / num_partes) * 100
                self.barra_progresso["value"] = progresso
                self.label_status.config(text=f"Cortando vídeo... Parte {i + 1}/{num_partes}")
                self.root.update_idletasks()

            messagebox.showinfo("Sucesso", f"Vídeo cortado em {num_partes} partes com sucesso!")
            self.label_status.config(text=f"Corte concluído! Salvo em: {dir_cortes}")
            self.barra_progresso["value"] = 100
            webbrowser.open(dir_cortes)

        except Exception as e:
            logging.error(f"Erro ao cortar vídeo: {e}")
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
        finally:
            self.barra_progresso["value"] = 0
            self.label_status.config(text="Pronto para novos downloads")
            janela_corte.destroy()

    def cortar_video_avancado(self):
        arquivo_video = filedialog.askopenfilename(
            title="Selecione o vídeo para cortar",
            filetypes=[("Vídeos", "*.mp4 *.avi *.mov *.mkv"), ("Todos os arquivos", "*.*")]
        )

        if not arquivo_video:
            return

        duracao_total = self.editor.obter_duracao(arquivo_video)
        if duracao_total <= 0:
            return

        janela_corte = tk.Toplevel(self.root)
        janela_corte.title("Corte Avançado de Vídeo")
        janela_corte.geometry("600x550")
        centralizar_janela(janela_corte, 600, 550)

        # Variáveis para controle
        inicio_var = tk.DoubleVar(value=0)
        fim_var = tk.DoubleVar(value=duracao_total)
        playing_var = tk.BooleanVar(value=False)

        # Frame principal
        frame_principal = tk.Frame(janela_corte)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas para visualização
        canvas_preview = tk.Canvas(frame_principal, bg='black', height=200)
        canvas_preview.pack(fill=tk.X, pady=5)
        canvas_preview_image = None

        # Controles de reprodução
        frame_controles = tk.Frame(frame_principal)
        frame_controles.pack(fill=tk.X, pady=5)

        btn_play = tk.Button(frame_controles, text="▶ Play", command=lambda: play_preview(), width=8)
        btn_play.pack(side=tk.LEFT, padx=5)

        btn_stop = tk.Button(frame_controles, text="⏹ Stop", command=lambda: stop_preview(), width=8)
        btn_stop.pack(side=tk.LEFT, padx=5)
        btn_stop.config(state=tk.DISABLED)

        # Sliders
        frame_sliders = tk.Frame(frame_principal)
        frame_sliders.pack(fill=tk.X, pady=10)

        tk.Label(frame_sliders, text="Início:").pack(anchor='w')
        slider_inicio = tk.Scale(frame_sliders, from_=0, to=duracao_total, variable=inicio_var,
                                 orient=tk.HORIZONTAL, length=550, resolution=1, command=lambda x: atualizar_preview())
        slider_inicio.pack()

        tk.Label(frame_sliders, text="Fim:").pack(anchor='w', pady=(10, 0))
        slider_fim = tk.Scale(frame_sliders, from_=0, to=duracao_total, variable=fim_var,
                              orient=tk.HORIZONTAL, length=550, resolution=1, command=lambda x: atualizar_preview())
        slider_fim.set(duracao_total)
        slider_fim.pack()

        # Labels de tempo
        frame_tempos = tk.Frame(frame_principal)
        frame_tempos.pack(fill=tk.X)

        label_tempos = tk.Label(frame_tempos, text="00:00:00 - 00:00:00")
        label_tempos.pack(side=tk.LEFT)

        label_duracao = tk.Label(frame_tempos, text="Duração do corte: 00:00:00")
        label_duracao.pack(side=tk.RIGHT)

        # Botões de ação
        frame_botoes = tk.Frame(frame_principal)
        frame_botoes.pack(fill=tk.X, pady=(20, 10))

        btn_cortar = tk.Button(frame_botoes, text="Cortar Vídeo", command=lambda: executar_corte_avancado(),
                               height=2, width=15)
        btn_cortar.pack(side=tk.RIGHT, padx=5)

        btn_cancelar = tk.Button(frame_botoes, text="Cancelar", command=janela_corte.destroy,
                                 height=2, width=15)
        btn_cancelar.pack(side=tk.RIGHT, padx=5)

        def atualizar_tempos():
            inicio = inicio_var.get()
            fim = fim_var.get()

            if inicio > fim:
                inicio_var.set(fim)
                inicio = fim

            if fim < inicio:
                fim_var.set(inicio)
                fim = inicio

            label_tempos.config(text=f"{formatar_tempo(inicio)} - {formatar_tempo(fim)}")
            label_duracao.config(text=f"Duração do corte: {formatar_tempo(fim - inicio)}")

        def gerar_preview():
            nonlocal canvas_preview_image
            canvas_preview.delete("all")
            frame_time = (inicio_var.get() + fim_var.get()) / 2
            temp_image = self.editor.gerar_frame_preview(arquivo_video, frame_time, 580, 190)

            if temp_image:
                try:
                    img = Image.open(temp_image)
                    img.thumbnail((580, 190))
                    canvas_preview_image = ImageTk.PhotoImage(img)
                    canvas_preview.create_image(0, 0, anchor='nw', image=canvas_preview_image)
                    canvas_preview.create_text(10, 10, text=f"Pré-visualização: {formatar_tempo(frame_time)}",
                                               fill="white", anchor='nw', font=('Arial', 10, 'bold'))
                except Exception as e:
                    logging.error(f"Erro ao carregar preview: {e}")

        def atualizar_preview():
            self.editor.stop_preview()
            atualizar_tempos()
            gerar_preview()
            btn_play.config(state=tk.NORMAL)
            btn_stop.config(state=tk.DISABLED)

        def play_preview():
            if playing_var.get():
                return

            playing_var.set(True)
            btn_play.config(state=tk.DISABLED)
            btn_stop.config(state=tk.NORMAL)

            success = self.editor.play_preview(
                arquivo_video,
                inicio_var.get(),
                fim_var.get(),
                (janela_corte.winfo_x(), janela_corte.winfo_y()),
                (janela_corte.winfo_width(), janela_corte.winfo_height())
            )

            if not success:
                messagebox.showerror("Erro", "Falha ao reproduzir pré-visualização")
                stop_preview()

        def stop_preview():
            playing_var.set(False)
            self.editor.stop_preview()
            btn_play.config(state=tk.NORMAL)
            btn_stop.config(state=tk.DISABLED)
            gerar_preview()

        def executar_corte_avancado():
            inicio = inicio_var.get()
            fim = fim_var.get()

            if inicio >= fim:
                messagebox.showerror("Erro", "O tempo de início deve ser menor que o tempo de fim")
                return

            duracao = fim - inicio
            if duracao < 1:
                messagebox.showerror("Erro", "A duração deve ser de pelo menos 1 segundo")
                return

            nome_base = os.path.splitext(os.path.basename(arquivo_video))[0]
            arquivo_saida = filedialog.asksaveasfilename(
                title="Salvar vídeo cortado como",
                initialdir=os.path.dirname(arquivo_video),
                initialfile=f"{nome_base}_cortado.mp4",
                defaultextension=".mp4",
                filetypes=[("Vídeo MP4", "*.mp4"), ("Todos os arquivos", "*.*")]
            )

            if not arquivo_saida:
                return

            janela_corte.destroy()
            self.label_status.config(text="Cortando vídeo...")
            self.barra_progresso["value"] = 0
            self.root.update_idletasks()

            success = self.editor.cortar_video(
                arquivo_video,
                arquivo_saida,
                inicio,
                duracao
            )

            if success:
                messagebox.showinfo("Sucesso", "Vídeo cortado com sucesso!")
                self.label_status.config(text=f"Corte concluído: {arquivo_saida}")
                self.barra_progresso["value"] = 100
                webbrowser.open(os.path.dirname(arquivo_saida))
            else:
                messagebox.showerror("Erro", "Falha ao cortar o vídeo")
                self.label_status.config(text="Erro no corte do vídeo")
                self.barra_progresso["value"] = 0

        # Inicialização
        atualizar_preview()
        janela_corte.protocol("WM_DELETE_WINDOW", lambda: [self.editor.stop_preview(), janela_corte.destroy()])