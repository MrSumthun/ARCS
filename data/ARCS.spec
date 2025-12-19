# -*- mode: python ; coding: utf-8 -*-
import os

# This spec is self-contained and resolves paths relative to this file.
# It allows running `pyinstaller data/ARCS.spec` from the repository root.
# Note: When PyInstaller executes a spec, `__file__` may not be defined; fall back to
# using the repo cwd + 'data' directory so the spec still resolves resources.

if '__file__' in globals():
    here = os.path.abspath(os.path.dirname(__file__))
else:
    here = os.path.abspath(os.path.join(os.getcwd(), 'data'))

project_root = os.path.abspath(os.path.join(here, '..'))
script_path = os.path.join(project_root, 'arcs.py')

# Include the data directory (bundle as 'data') and the icons next to the spec
datas = [
    (here, 'data'),
]

a = Analysis(
    [script_path],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=['arcs_utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ARCS',
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
    icon=[os.path.join(here, 'app.icns')],
)
app = BUNDLE(
    exe,
    name='ARCS.app',
    icon=os.path.join(here, 'app.icns'),
    bundle_identifier=None,
)
