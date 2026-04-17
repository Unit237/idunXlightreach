#!/usr/bin/env bash
set -euo pipefail

echo "Checking Idun agent health..."
curl -fsS "http://localhost:8800/health" >/dev/null
echo "OK: http://localhost:8800/health"

echo "Checking Idun docs..."
curl -fsS "http://localhost:8800/docs" >/dev/null
echo "OK: http://localhost:8800/docs"

echo "Smoke test passed."
