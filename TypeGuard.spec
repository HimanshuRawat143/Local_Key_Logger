# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['typeguard\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('typeguard\\assets\\templates\\dashboard.html', 'typeguard\\assets\\templates')],
    hiddenimports=['pynput.keyboard._win32', 'pynput.mouse._win32', 'pystray._win32', 'typeguard.install'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TypeGuard',
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
)
