import os
import re
import sys
import winreg

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def centralizar_janela(janela, largura, altura):
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f'{largura}x{altura}+{x}+{y}')

def formatar_tempo(segundos):
    horas, resto = divmod(int(segundos), 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def formatar_tamanho(bytes):
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.2f} KB"
    elif bytes < 1024 * 1024 * 1024:
        return f"{bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes / (1024 * 1024 * 1024):.2f} GB"

def limpar_nome_arquivo(nome):
    nome = re.sub(r'[<>:"/\\|?*#]', '', nome)
    nome = nome.strip()
    nome = nome.replace('\n', ' ')
    return nome

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
            except Exception as e:
                logging.error(f"Erro ao adicionar ao PATH: {e}")