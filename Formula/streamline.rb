# Homebrew formula for StreamLine — installs the standalone macOS binary
# built by .github/workflows/release.yml, rather than declaring the whole
# FastAPI/uvicorn/pydantic dependency tree as Homebrew resources (pydantic
# includes a compiled Rust extension, which makes that approach fragile).
#
# This file lives in the main repo as a staging copy. To actually publish
# it as `brew install streamline`, copy it into a separate tap repository
# named `homebrew-streamline` under the same GitHub account — see
# docs/releases.md for the exact steps. Checksums below are filled in by
# scripts/update_homebrew_formula.py after a release is published; until
# then this formula will not install (the sha256 placeholders won't match).

class Streamline < Formula
  desc "Private, self-hosted chat — terminal and web interface"
  homepage "https://github.com/L1avZh/StreamLine"
  version "3.0.0"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/L1avZh/StreamLine/releases/download/v#{version}/StreamLine-macos-arm64"
      sha256 "REPLACE_WITH_ARM64_SHA256"
    end
    on_intel do
      url "https://github.com/L1avZh/StreamLine/releases/download/v#{version}/StreamLine-macos-x64"
      sha256 "REPLACE_WITH_X64_SHA256"
    end
  end

  def install
    binary = Hardware::CPU.arm? ? "StreamLine-macos-arm64" : "StreamLine-macos-x64"
    bin.install binary => "streamline"
  end

  test do
    assert_match "streamline, version #{version}", shell_output("#{bin}/streamline --version")
  end
end
