#!/usr/bin/env python3
"""Fill in the Homebrew formula's checksums after a GitHub Release is published.

Usage:
    python scripts/update_homebrew_formula.py v3.0.0

Downloads the released macOS binaries, computes their sha256, and updates
Formula/streamline.rb (and its `version` line) in place. Run this, review
the diff, then copy the file into the `homebrew-streamline` tap repo (see
docs/releases.md) and commit it there.
"""

from __future__ import annotations

import hashlib
import re
import sys
import urllib.request
from pathlib import Path

FORMULA_PATH = Path(__file__).resolve().parent.parent / "Formula" / "streamline.rb"
REPO = "L1avZh/StreamLine"
ASSETS = {
    "arm64": "StreamLine-macos-arm64",
    "x64": "StreamLine-macos-x64",
}


def sha256_of_url(url: str) -> str:
    print(f"Downloading {url} ...")
    digest = hashlib.sha256()
    with urllib.request.urlopen(url) as response:  # noqa: S310 - trusted GitHub releases URL
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].startswith("v"):
        raise SystemExit(f"Usage: {sys.argv[0]} vX.Y.Z")
    tag = sys.argv[1]
    version = tag.removeprefix("v")

    checksums = {}
    for arch, asset_name in ASSETS.items():
        url = f"https://github.com/{REPO}/releases/download/{tag}/{asset_name}"
        checksums[arch] = sha256_of_url(url)

    text = FORMULA_PATH.read_text(encoding="utf-8")
    text = re.sub(r'version "[^"]*"', f'version "{version}"', text, count=1)
    text = re.sub(r'sha256 "REPLACE_WITH_ARM64_SHA256"', f'sha256 "{checksums["arm64"]}"', text)
    text = re.sub(r'sha256 "REPLACE_WITH_X64_SHA256"', f'sha256 "{checksums["x64"]}"', text)
    # Also replace an already-filled-in sha256 on subsequent runs.
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "on_arm do" in line:
            _patch_next_sha256(lines, i, checksums["arm64"])
        if "on_intel do" in line:
            _patch_next_sha256(lines, i, checksums["x64"])
    FORMULA_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nUpdated {FORMULA_PATH} for {tag}.")


def _patch_next_sha256(lines: list[str], start: int, digest: str) -> None:
    for i in range(start, min(start + 4, len(lines))):
        if "sha256" in lines[i]:
            lines[i] = re.sub(r'sha256 "[^"]*"', f'sha256 "{digest}"', lines[i])
            return


if __name__ == "__main__":
    main()
