"""Entry point for the standalone (PyInstaller) build.

Not part of the installable Python package — only used when bundling
StreamLine into a single executable. `pip install streamline` uses the
`streamline.cli:cli` console-script entry point instead (see pyproject.toml).
"""

from streamline.cli import cli

if __name__ == "__main__":
    cli()
