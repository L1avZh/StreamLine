# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the standalone StreamLine executable.

Build with: pyinstaller packaging/streamline.spec
(see scripts/build_binary.sh for the full, reproducible build process —
it installs a real, non-editable copy of the package into a clean venv
first, since PyInstaller's static analysis doesn't reliably follow an
editable/dev install).

Paths are computed relative to this file (``SPECPATH``, provided by
PyInstaller) so the build works on any machine or CI runner, not just
the one it was written on.
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
STATIC_DIR = os.path.join(PROJECT_ROOT, "streamline", "web", "static")

a = Analysis(
    [os.path.join(SPECPATH, "entry_point.py")],
    pathex=[],
    binaries=[],
    datas=[(STATIC_DIR, "streamline/web/static")],
    hiddenimports=[],
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
    name="streamline",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX-compressed binaries trigger more antivirus false positives
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
