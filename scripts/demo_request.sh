#!/usr/bin/env bash
set -euo pipefail

# Sample on-call paste: repetitive structure + long context → good Compress compression demo.
curl -sS -X POST "http://localhost:8800/agent/run" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "demo-inc-1",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "SEV-2 | checkout API\nWindow: last 20m\nSymptoms: elevated 5xx from payments-api, p95 latency ~4s vs ~400ms baseline. Partial overlap with last week after a config rollout (INC-1891).\nTried: pod restart (no lasting effect), scale 6→10 replicas (partial relief).\nAsk: first mitigation checks in order, and whether we should roll back feature flag payments.dual-write.enabled (enabled ~2h ago)."
      }
    ]
  }'

echo ""
