# downvideos.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['C:\\downVideos'],  # Caminho do seu projeto
    binaries=[],
    datas=[
        ('downVideos.ico', '.'),      # Ícone
        ('downVideos.png', '.'),      # Imagem/logo
    ],
    hiddenimports=['yt_dlp', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='downVideos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # Oculta o terminal (True para depuração)
    icon='downVideos.ico',  # Ícone do executável
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)