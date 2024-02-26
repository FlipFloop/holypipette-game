# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['patch_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('holypipette/devices/camera/FakeMicroscopeImgs/*','.'),('holypipette/gui/tutorial_media/XBox.png','.'),('pressure','pressure')],
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
    [],
    exclude_binaries=True,
    name='Patch clamp simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Patch clamp simulator',
)
app = BUNDLE(
    coll,
    name='Patch clamp simulator.app',
    icon='holypipette.icns',
    bundle_identifier=None,
)
