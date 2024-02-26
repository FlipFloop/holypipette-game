# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['patch_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('holypipette/devices/camera/FakeMicroscopeImgs/*','.'),('holypipette/gui/tutorial_media/XBox.png','.'),('pressure','pressure'), ('.env','.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HolyPipette',
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
