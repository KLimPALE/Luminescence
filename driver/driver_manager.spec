import sys
import os
from pathlib import Path


driver_folders = ['cypress', 'ftdi', 'keysight', 'prolific']
driver_files = []

for folder in driver_folders:
    source_path = Path(folder)

    if source_path.exists():
        for file in source_path.iterdir():
            if file.is_file():
                driver_files.append((str(file), folder))

icon_path = 'icon.png'

if Path(icon_path).exists():
    driver_files.append((icon_path, '.'))

analysis = Analysis(
    ['driver_manager.py'],
    pathex=[],
    binaries=[],
    datas=driver_files,
    hiddenimports=['tkinter', 'threading'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name='DriverManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.png'
)
