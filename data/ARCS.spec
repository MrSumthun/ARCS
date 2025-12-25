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
    # Ensure PyQt6, Pillow and reportlab modules are discovered by PyInstaller
    hiddenimports=[
        'arcs_utils',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'PIL',
        'PIL.Image',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.lib.units',
        'reportlab.platypus',
        'reportlab.platypus.tables',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.pdfbase.ttfonts',
        'reportlab.rl_config',
    ],
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

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='ARCS',
)

app = BUNDLE(
    coll,
    name='ARCS.app',
    icon=os.path.join(here, 'app.icns'),
    bundle_identifier=None,
)
