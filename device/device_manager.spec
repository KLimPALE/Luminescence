from PyInstaller.utils.hooks import collect_all

files = [
    ('..\\library', 'library'),
    ('..\\sdk', 'sdk'),
    ('icon.png', '.')
]

binaries = []
imports = []

result = collect_all('pyvisa')
files += result[0]
binaries += result[1]
imports += result[2]
result = collect_all('pyvisa_py')
files += result[0]
binaries += result[1]
imports += result[2]
result = collect_all('pyvisa-py')
files += result[0]
binaries += result[1]
imports += result[2]
result = collect_all('usb')
files += result[0]
binaries += result[1]
imports += result[2]
result = collect_all('serial')
files += result[0]
binaries += result[1]
imports += result[2]

analysis = Analysis(
    ['device_manager.py'],
    pathex=[],
    binaries=binaries,
    datas=files,
    hiddenimports=imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name='DeviceManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.png',
)
