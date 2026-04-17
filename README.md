# Idun x LightReach (Compress) Public Demo

A small, copy-paste friendly reference for running an **Idun Agent Engine** LangGraph workflow where every LLM call goes through **LightReach’s hosted Compress API** (routing + optional prompt compression + cost metadata).

This demo intentionally does **not** run Compress locally. Compress is a cloud service.

## What this demo proves

- Idun can serve a LangGraph agent over HTTP (`/agent/run`, OpenAPI docs at `/docs`).
- The agent can call Compress using your **LightReach API key** (`lr_…`) and your **BYOK provider keys** configured in the LightReach dashboard.
- You can keep responsibilities cleanly separated:
  - **Idun**: agent API/runtime + graph orchestration
  - **Compress**: cross-provider routing, compression, and cost attribution

## Example agent: incident triage copilot

This is intentionally aligned with how [Idun Platform](https://idunplatform.com/) positions production agents: a **stable HTTP API**, **LangGraph** orchestration, and **durable conversation state** (this demo uses SQLite checkpoints in `config.yaml`; swap for Postgres when you harden).

The graph implements a small **internal on-call copilot**: if the user does not supply a `system` message, the agent prepends a **triage-focused system prompt** (concise bullets, no invented logs, mitigation-first). That is the kind of behavior product and platform teams wrap behind an API — not a toy “hello world.”

Downstream, LightReach Compress is a better fit than hand-rolling provider clients: same request can be routed across your BYOK universe under an **HLE floor**, with **optional input compression** (helpful when on-call pastes repeat boilerplate), and **`tags`** for attribution (`COMPRESS_TAG_*`).

With `POST /api/v2/complete`, the demo can append a short **metadata footer** (model, provider, rough cost, compression token delta) so stakeholders see routing transparency without spelunking logs. Turn it off with `COMPRESS_APPEND_META_FOOTER=false`.

## Architecture

```text
User/App
  -> Idun Agent Engine (LangGraph workflow)
    -> LightReach Compress API
      -> Routed upstream provider model (OpenAI/Anthropic/Google/…)
```

## Prerequisites

- A LightReach account and API key (`lr_…`)
- At least one upstream provider key added in the LightReach dashboard (**BYOK**)

Docs:

- Sign up: [compress.lightreach.io/signup](https://compress.lightreach.io/signup)
- Native completion endpoint used by default in this demo: [`POST /api/v2/complete`](https://compress.lightreach.io/api/v2/complete)

## Quickstart (Docker)

1) Create your env file:

```bash
cd examples/idun_compress_agent
cp stack.env.example stack.env
```

2) Set your LightReach key in `stack.env`:

```env
COMPRESS_API_KEY=lr_…
```

3) Start Idun Agent Engine:

```bash
docker compose --env-file stack.env up --build
```

4) Verify Idun is up:

```bash
curl -fsS http://localhost:8800/health
curl -fsS http://localhost:8800/docs >/dev/null && echo "OK: /docs"
```

5) Run a request through Idun → Compress (realistic on-call paste — verbose prompts compress well):

```bash
curl -sS -X POST http://localhost:8800/agent/run \
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
```

Helper scripts:

```bash
bash scripts/smoke_test.sh
bash scripts/demo_request.sh
```

## Configuration

Defaults are chosen to match the public docs:

- **Default mode**: `POST /api/v2/complete` via `COMPRESS_V2_URL`
- **Optional mode**: OpenAI-compatible `POST /chat/completions` via `COMPRESS_OPENAI_BASE_URL` (set `COMPRESS_USE_OPENAI_COMPAT=1`)

Common knobs (see `stack.env.example`):

- `COMPRESS_API_KEY` (required)
- `COMPRESS_V2_URL` (defaults to `https://compress.lightreach.io/api/v2/complete`)
- `COMPRESS_DESIRED_HLE` (defaults to `25`)
- `COMPRESS_COMPRESS` (defaults to `true`)
- `COMPRESS_LLM_PROVIDER` (optional provider constraint)
- `COMPRESS_TAG_*` (optional attribution tags)
- `AGENT_SYSTEM_PROMPT` (optional; overrides the built-in triage system prompt)
- `COMPRESS_APPEND_META_FOOTER` (default `true` for v2 demos; appends routing/cost/compression lines)

## Files in this demo

- `agent.py` - LangGraph workflow (triage system prompt + Compress call + optional v2 metadata footer)
- `config.yaml` - Idun file-based engine config
- `docker-compose.yml` - Idun-only Docker stack
- `stack.env.example` - environment template
- `Dockerfile` - Idun agent image
- `docker_entrypoint.sh` - starts Idun engine on `0.0.0.0`
- `scripts/smoke_test.sh` - health and docs checks
- `scripts/demo_request.sh` - sends a sample request to `/agent/run`

## Common pitfalls

### 1) `COMPRESS_API_KEY is not set`

The container will start, but model calls will fail until you set a real `lr_…` key in `stack.env`.

### 2) Completions fail with upstream/provider errors

Compress routes using the provider keys you configured in the LightReach dashboard. If no usable provider key exists for the selected route, requests fail upstream.

### 3) `localhost:8800` not reachable but logs look healthy

Idun’s CLI defaults to binding `localhost` inside containers. This demo starts the engine with `host=0.0.0.0` from `docker_entrypoint.sh`.

If needed:

```bash
docker compose --env-file stack.env build --no-cache idun-agent
docker compose --env-file stack.env up
```

### 4) Full Idun platform port clashes

This demo only runs Idun Agent Engine on **8800**. If you also run the full Idun platform stack, avoid double-booking ports on your machine.

## Using the full Idun platform UI (optional)

This demo uses Idun Agent Engine only. If you want the full Idun Manager/Web UI:

```bash
git clone https://github.com/Idun-Group/idun-agent-platform.git
cd idun-agent-platform
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

Then enroll your agent and point `graph_definition` to:

`./examples/idun_compress_agent/agent.py:workflow`

## Public sharing template

Use this short description in your repo:

> "A runnable reference showing how to deploy an Idun-managed LangGraph agent that sends LLM inference traffic through LightReach’s hosted Compress API for routing, optional compression, and cost attribution."

## References

- [Idun Platform](https://idunplatform.com/)
- [LightReach / Compress docs](https://compress.lightreach.io/)
- [Idun Agent Platform](https://github.com/Idun-Group/idun-agent-platform)
- [Idun LangGraph guide](https://docs.idunplatform.com/guides/langgraph-production-deployment)
