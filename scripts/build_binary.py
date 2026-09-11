#!/usr/bin/env python3
"""Build the standalone StreamLine executable for the current platform.

Builds from a clean, non-editable install in a throwaway virtual
environment — PyInstaller's static import analysis doesn't reliably
follow an editable/dev install, and a release build should reflect
exactly what `pip install .` produces, not whatever happens to be on
the developer's PYTHONPATH.

Usage:
    python scripts/build_binary.py

Output: dist/streamline (dist/streamline.exe on Windows)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_VENV = ROOT / ".build-venv"
SPEC_FILE = ROOT / "packaging" / "streamline.spec"


def run(*args: str) -> None:
    print(f"+ {' '.join(args)}", flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def main() -> None:
    for stale in (BUILD_VENV, ROOT / "build" / "pyinstaller", ROOT / "dist"):
        if stale.exists():
            shutil.rmtree(stale)

    print(f"Creating build environment at {BUILD_VENV} ...")
    venv.EnvBuilder(with_pip=True, clear=True).create(BUILD_VENV)
    python = str(venv_python(BUILD_VENV))

    run(python, "-m", "pip", "install", "--upgrade", "pip")
    run(python, "-m", "pip", "install", str(ROOT))
    run(python, "-m", "pip", "install", "pyinstaller>=6.0")
    run(
        python,
        "-m",
        "PyInstaller",
        str(SPEC_FILE),
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(ROOT / "build" / "pyinstaller"),
        "--noconfirm",
    )

    binary = ROOT / "dist" / ("streamline.exe" if sys.platform == "win32" else "streamline")
    if not binary.exists():
        raise SystemExit(f"Build finished but {binary} was not produced.")
    print(f"\nBuilt {binary} ({binary.stat().st_size / 1_000_000:.1f} MB)")

    print("Verifying the binary actually runs ...")
    run(str(binary), "--version")


if __name__ == "__main__":
    main()
