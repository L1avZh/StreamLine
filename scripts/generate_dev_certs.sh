#!/usr/bin/env bash
# Generates a throwaway self-signed TLS certificate for local development.
# Never commit the resulting files; they are covered by .gitignore.
set -euo pipefail

out_dir="${1:-./certs}"
mkdir -p "$out_dir"

openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
  -keyout "$out_dir/key.pem" \
  -out "$out_dir/cert.pem" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Wrote $out_dir/cert.pem and $out_dir/key.pem (self-signed, localhost only)."
echo "Start the server with: streamline server --certfile $out_dir/cert.pem --keyfile $out_dir/key.pem"
