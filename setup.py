import sys
import os
from cx_Freeze import setup, Executable

# Directory principale del progetto
base_dir = os.path.abspath(os.path.dirname(__file__))

# Determina se siamo su Windows
is_windows = sys.platform.startswith('win')

# Base per l'eseguibile
base = 'Win32GUI' if is_windows else None

# File e directory da includere
include_files = [
    # Includi la directory delle icone
    ('icons', 'icons'),
    # Includi la directory per Linux se presente
    ('linux', 'linux')
]

# Opzioni per il build
build_options = {
    'packages': [
        'os',
        'sys',
        'subprocess',
        'tempfile',
        'shutil',
        'zipfile',
        'json',
        'requests',
        'PyQt6',
        'mutagen',
        'array',
        'wave',
        'numpy',
    ],
    'excludes': [],
    'include_files': include_files,
    'include_msvcr': True,  # Include the Visual C runtime files
}

# Creazione dell'eseguibile
executables = [
    Executable(
        script='main.py',
        base=base,
        target_name='dBPrecision.exe' if is_windows else 'dBPrecision',
        icon='icons/dbprecision.ico' if os.path.exists(os.path.join(base_dir, 'icons/dbprecision.ico')) else None,
        shortcut_name='dBPrecision',
        shortcut_dir='DesktopFolder',
        copyright='Copyright 2025 dBPrecision. Tutti i diritti riservati.',
    )
]

# Configurazione setup
setup(
    name='dBPrecision',
    version='1.1.0',
    description='Applicazione per normalizzare il volume dei file MP3',
    author='Alessio Abrugiati',
    options={'build_exe': build_options},
    executables=executables
)
