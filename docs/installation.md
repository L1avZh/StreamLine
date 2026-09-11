# Installation

Pick whichever fits how you work. None of them require you to understand Python.

## Standalone executable (no Python required)

Download the file for your platform from the
[latest release](https://github.com/L1avZh/StreamLine/releases/latest):

| Platform | File |
|---|---|
| macOS (Apple Silicon) | `StreamLine-macos-arm64` |
| macOS (Intel) | `StreamLine-macos-x64` |
| Windows | `StreamLine-windows-x64.exe` |
| Linux | `StreamLine-linux-x64` |

**macOS / Linux:**

```bash
chmod +x StreamLine-macos-arm64   # match the file you downloaded
./StreamLine-macos-arm64
```

macOS will warn that the file is from an unidentified developer the first time (it isn't
notarized yet — see [releases.md](releases.md)). Right-click the file → **Open** once to
approve it, or run `xattr -d com.apple.quarantine StreamLine-macos-arm64`.

**Windows:** double-click `StreamLine-windows-x64.exe`. Windows Defender SmartScreen may warn
about an unrecognized publisher the first time — click **More info → Run anyway**. If you'd
rather not click through that, use the Python package install instead (see below).

## Homebrew (macOS)

Not published yet — this requires a one-time `homebrew-streamline` tap repository to be created
(see [releases.md](releases.md) for the exact steps). Once it exists:

```bash
brew tap L1avZh/streamline
brew install streamline
```

## Python package (PyPI)

**Not published yet.** The name `streamline` on PyPI belongs to an unrelated project — publishing
under a different name (e.g. `streamline-chat`) is tracked in
[releases.md](releases.md#publishing-to-pypi). Until that's resolved, use **From source** below.

## From source

```bash
git clone https://github.com/L1avZh/StreamLine.git
cd StreamLine
pip install .
streamline
```

See [development.md](development.md) if you want to modify StreamLine rather than just run it.

## Docker (server only)

For running just the chat server headlessly (not the CLI menu or web interface):

```bash
docker build -t streamline .
docker run --rm -p 54140:54140 streamline
```
