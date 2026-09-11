# Releases

## Versioning

StreamLine follows [Semantic Versioning](https://semver.org/). The version is declared in exactly
one place, `streamline/__init__.py` (`__version__`), and mirrored in `pyproject.toml`'s
`[project].version` — both must be bumped together. `streamline --version` reads the former at
runtime.

No version has been tagged/released yet; `3.0.0` is the target for the first public release, not
a bump from something already shipped.

## Changelog

Kept by hand in [CHANGELOG.md](../CHANGELOG.md), [Keep a Changelog](https://keepachangelog.com/)
style. Add an entry under a new version heading as part of the PR that changes behavior —
don't batch it up after the fact.

## Cutting a release

1. Update the version in `streamline/__init__.py` and `pyproject.toml`, and add a
   `CHANGELOG.md` entry. Merge that to `main`.
2. Tag and push:

   ```bash
   git tag v3.0.0
   git push origin v3.0.0
   ```

3. This triggers `.github/workflows/release.yml`, which:
   - builds the wheel + sdist and validates them with `twine check`
   - builds a standalone executable for macOS (arm64 + Intel), Windows, and Linux
   - creates a **draft** GitHub Release with everything attached

4. Open the draft release, sanity-check the artifact list, edit the auto-generated notes if
   needed, and publish it. It stays a draft until you do this deliberately — nothing goes out
   automatically on a tag push.

## Building artifacts locally

```bash
# Python package (wheel + sdist)
pip install -e ".[packaging]"
python -m build
twine check dist/*

# Standalone executable for the current platform
python scripts/build_binary.py
```

`scripts/build_binary.py` builds from a clean, non-editable install in a throwaway virtual
environment — this matters because PyInstaller's static import analysis doesn't reliably follow
an editable/dev install, and a release build should reflect exactly what `pip install .` produces.

## Publishing to PyPI

Not automatic. `publish-to-pypi` in `release.yml` is a manually-triggered job
(**Actions → Release → Run workflow**, tick "Also publish to PyPI") gated behind a `pypi`
GitHub Environment, using [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC) — no API token to manage or leak. One-time setup, before the first publish:

1. On PyPI, create the `streamline` project (or claim the name) and add a trusted publisher
   pointing at this repo (`L1avZh/StreamLine`), workflow file `release.yml`, environment `pypi`.
2. In this repo's GitHub settings, create an environment named `pypi` (optionally with required
   reviewers, for an extra manual gate before publishing).

Until that's configured, the job will fail harmlessly if triggered — it does not silently no-op.

## Publishing to Homebrew

There is no `homebrew-streamline` tap yet — `Formula/streamline.rb` in this repo is a staging
copy, not a live formula. To make `brew install streamline` real:

1. Create a new GitHub repository named `homebrew-streamline` under the same account.
2. After a release is published, compute its checksums and update the formula:

   ```bash
   python scripts/update_homebrew_formula.py v3.0.0
   ```

3. Copy the updated `Formula/streamline.rb` into the tap repo (same path: `Formula/streamline.rb`)
   and commit it there.
4. Users can then run:

   ```bash
   brew tap L1avZh/streamline
   brew install streamline
   ```

The formula installs the standalone macOS binary directly rather than declaring StreamLine's full
dependency tree as Homebrew resources — `pydantic` (a FastAPI dependency) ships a compiled Rust
extension, which makes the resource-based approach fragile to maintain for a fast-moving stack
like this one.

## Code signing / notarization

Not implemented. The standalone macOS and Windows binaries are unsigned, so Gatekeeper/SmartScreen
will warn on first run (see [installation.md](installation.md) for how to get past that). Adding
this requires an Apple Developer account (for `codesign`/`notarytool`) and a code-signing
certificate (for Windows) that this project doesn't currently have — the build is structured so
signing steps can be inserted into `release.yml` later without other changes.

## Update checking

Not implemented. There's no auto-updater and no background "phone home" of any kind — see
[security.md](security.md). If a manual "check for updates" feature is added later, it would be
one explicit HTTP request the user triggers (e.g. `streamline settings` → an "check for updates"
action), comparing against the latest GitHub Release tag, never a silent background check and
never code executed automatically as a result.
