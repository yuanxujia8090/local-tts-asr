#!/bin/bash
# Quick API smoke test — run after starting the server

BASE="http://localhost:8000/v1"

echo "=== Health Check ==="
curl -s $BASE/health | python3 -m json.tool

echo ""
echo "=== List Models ==="
curl -s $BASE/models | python3 -m json.tool

echo ""
echo "=== TTS Test (text only, no engine) ==="
curl -s -X POST $BASE/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "model": "qwen3-tts"}' \
  -o /tmp/test_tts.wav 2>&1 || echo "(Expected: engine not loaded — check logs)"

echo ""
echo "=== Done ==="
