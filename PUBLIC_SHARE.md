# Public Share Kit

Use this file as copy you can reuse in a public repo or LinkedIn post.

## Repo subtitle

`Idun-managed LangGraph agent with LightReach Compress as the hosted model gateway (routing + optimization).`

## Short repo description

This demo ships a **realistic internal “incident triage copilot”** on Idun Agent Engine: production-style `/agent/run` API, SQLite-backed checkpoints for threaded conversations, and every completion routed through LightReach’s hosted Compress API (`POST /api/v2/complete` by default). Tags attribute spend; optional footers surface model, cost, and compression stats for demos.

## Why this example (mapped to Idun + Compress)

From [Idun Platform](https://idunplatform.com/), teams care about shipping LangGraph agents to production with a **standard API**, **memory persistence**, and a path to **governance and observability** on the full stack. This repo focuses on the **engine slice** you can run today: Idun serves the graph and persists threads; LightReach Compress handles **cross-provider routing**, **prompt compression**, and **deterministic cost signals** (BYOK provider keys stay in the LightReach dashboard).

The sample agent is deliberately boring-in-a-good-way: **platform on-call triage** (symptoms, mitigations, rollback vs scale vs flag) — the kind of workflow internal platform teams already wrap behind HTTP.

## LinkedIn draft (long)

Shipping agents to production is rarely “call an LLM once.” It’s an API surface, threaded state, and (eventually) guardrails + observability — the shape [Idun Platform](https://idunplatform.com/) is built around.

We put together a small reference integration that matches how platform teams actually think about the boundary:

**Idun (agent runtime)**  
- LangGraph workflow behind Idun Agent Engine’s REST API (`/agent/run`)  
- Conversation checkpoints (SQLite in the demo) so `thread_id` means something in real incidents  

**LightReach Compress (hosted inference economics)**  
- One LightReach API key + BYOK provider keys in the dashboard  
- `POST /api/v2/complete` for routing under an HLE floor, optional lossless input compression, and tags so finance can see *which team / feature / env* drove spend  

The demo scenario is an **internal incident triage copilot**: on-call paste, tight bullets, safe mitigations first — then the response footer shows which model ran and what it roughly cost (great for screenshots in internal reviews).

If you’re standardizing agent delivery without losing control of model spend, this split is the point: **sovereign agent serving** on your side, **routing + receipts** on the compress side.

*(Swap “SQLite demo” for Postgres + wire Idun Manager when you want the full governance/control plane from the same project.)*

## LinkedIn draft (short)

Idun for production agent APIs + memory. LightReach Compress for hosted routing, compression, and cost tags.  
We open-sourced a runnable **incident triage copilot** that shows the split cleanly — LangGraph on Idun, `POST /api/v2/complete` on LightReach, BYOK keys in the dashboard.

Details: [Idun Platform](https://idunplatform.com/) · [LightReach / Compress](https://compress.lightreach.io/)

## One-line hook options

- “We split **agent serving** (Idun) from **model economics** (LightReach Compress) — here’s a runnable incident copilot that proves it.”
- “Same LangGraph agent your team writes — now with routing + compression + cost receipts without baking provider keys into the agent container.”
