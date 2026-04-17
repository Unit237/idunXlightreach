import json
import os
from typing import Any

import requests
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, MessagesState, StateGraph

load_dotenv()

# Default persona for the public demo: a small internal copilot teams actually ship behind an API.
# Idun owns the graph + HTTP surface + (with full platform) guardrails/observability; Compress owns routing + spend.
DEFAULT_SYSTEM_PROMPT = """You are an internal platform incident triage assistant.

Rules:
- Be concise. Use short bullets and clear next actions.
- If the user paste is ambiguous, ask at most one clarifying question.
- Do not invent logs, metrics, stack traces, or ticket IDs that are not present in the user message.
- Prefer safe, reversible mitigation steps (rollback, scale, feature flag, traffic shed) over speculative root cause.
"""


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text" and isinstance(part.get("text"), str):
                    text_parts.append(part["text"])
                else:
                    text_parts.append(json.dumps(part, ensure_ascii=False))
            else:
                text_parts.append(str(part))
        return "\n".join(part for part in text_parts if part)
    if content is None:
        return ""
    return str(content)


def _to_openai_message(message: BaseMessage) -> dict[str, Any]:
    if isinstance(message, SystemMessage):
        role = "system"
    elif isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, ToolMessage):
        role = "tool"
    else:
        role = "assistant"

    payload: dict[str, Any] = {
        "role": role,
        "content": _normalize_content(message.content),
    }

    if role == "tool":
        tool_call_id = getattr(message, "tool_call_id", None)
        if tool_call_id:
            payload["tool_call_id"] = tool_call_id

    if role == "assistant":
        tool_calls = getattr(message, "tool_calls", None)
        if isinstance(tool_calls, list) and tool_calls:
            payload["tool_calls"] = tool_calls
            if not payload["content"]:
                payload["content"] = None

    return payload


def _api_messages(state: MessagesState) -> list[dict[str, Any]]:
    """Build OpenAI-shaped messages for Compress, ensuring a system prompt exists."""
    converted = [_to_openai_message(message) for message in state["messages"]]
    if any(message.get("role") == "system" for message in converted):
        return converted
    system_content = os.getenv("AGENT_SYSTEM_PROMPT", "").strip() or DEFAULT_SYSTEM_PROMPT
    return [{"role": "system", "content": system_content}, *converted]


def _compress_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("COMPRESS_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _compress_tags() -> dict[str, str]:
    tags = {
        "team": os.getenv("COMPRESS_TAG_TEAM", "").strip(),
        "environment": os.getenv("COMPRESS_TAG_ENVIRONMENT", "").strip(),
        "feature": os.getenv("COMPRESS_TAG_FEATURE", "").strip(),
    }
    return {key: value for key, value in tags.items() if value}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _v2_meta_footer(body: dict[str, Any]) -> str | None:
    if not _env_bool("COMPRESS_APPEND_META_FOOTER", True):
        return None
    lines: list[str] = []
    routing = body.get("routing_info")
    if isinstance(routing, dict):
        sel = routing.get("selected_model") or body.get("model_used")
        prov = routing.get("selected_provider") or body.get("provider_used")
        req_hle = routing.get("requested_hle")
        eff_hle = routing.get("effective_hle")
        if sel:
            lines.append(f"model: {sel}")
        if prov:
            lines.append(f"provider: {prov}")
        if req_hle is not None and eff_hle is not None:
            lines.append(f"HLE requested/effective: {req_hle}/{eff_hle}")
    else:
        if body.get("model_used"):
            lines.append(f"model: {body['model_used']}")
        if body.get("provider_used"):
            lines.append(f"provider: {body['provider_used']}")
    cost = body.get("cost_estimate")
    if cost is not None:
        try:
            lines.append(f"estimated cost (USD): {float(cost):.6f}")
        except (TypeError, ValueError):
            lines.append(f"estimated cost: {cost}")
    stats = body.get("compression_stats")
    if isinstance(stats, dict) and stats.get("compression_enabled"):
        savings = stats.get("token_savings")
        orig = stats.get("original_tokens")
        comp = stats.get("compressed_tokens")
        if savings is not None and orig is not None and comp is not None:
            lines.append(f"input tokens: {orig} → {comp} (saved {savings})")
    if not lines:
        return None
    return "\n---\n" + "\n".join(lines)


def _openai_base_url() -> str:
    explicit = os.getenv("COMPRESS_OPENAI_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")

    legacy = os.getenv("COMPRESS_BASE_URL", "").strip()
    if legacy:
        legacy = legacy.rstrip("/")
        if legacy.endswith("/v2/complete"):
            raise ValueError(
                "COMPRESS_BASE_URL looks like a /v2/complete URL. "
                "Set COMPRESS_V2_URL instead (or use COMPRESS_OPENAI_BASE_URL for OpenAI-compatible mode)."
            )
        return legacy

    return "https://api.compress.lightreach.io/v1"


def _v2_complete_url() -> str:
    explicit = os.getenv("COMPRESS_V2_URL", "").strip()
    if explicit:
        return explicit

    legacy = os.getenv("COMPRESS_BASE_URL", "").strip()
    if legacy:
        legacy = legacy.rstrip("/")
        if legacy.endswith("/v2/complete"):
            return legacy

    return "https://compress.lightreach.io/api/v2/complete"


def _compress_mode() -> str:
    if _env_bool("COMPRESS_USE_OPENAI_COMPAT", False):
        return "openai_compat"
    return "v2_complete"


def call_compress(state: MessagesState) -> dict[str, list[AIMessage]]:
    mode = _compress_mode()
    model = os.getenv("COMPRESS_MODEL", "lightreach").strip() or "lightreach"
    llm_provider = os.getenv("COMPRESS_LLM_PROVIDER", "").strip().lower()
    timeout = float(os.getenv("COMPRESS_REQUEST_TIMEOUT", "120"))

    api_key = os.getenv("COMPRESS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("COMPRESS_API_KEY is not set (expected a LightReach key: lr_…).")

    tags = _compress_tags()

    if mode == "openai_compat":
        base_url = _openai_base_url()
        payload: dict[str, Any] = {
            "model": model,
            "messages": _api_messages(state),
        }
        if tags:
            payload["tags"] = tags
        if llm_provider:
            payload["llm_provider"] = llm_provider
        url = f"{base_url}/chat/completions"
    else:
        desired_hle_raw = os.getenv("COMPRESS_DESIRED_HLE", "25").strip()
        desired_hle = float(desired_hle_raw) if desired_hle_raw else 25.0
        compress_enabled = _env_bool("COMPRESS_COMPRESS", True)

        payload = {
            "messages": _api_messages(state),
            "desired_hle": desired_hle,
            "compress": compress_enabled,
        }
        if tags:
            payload["tags"] = tags
        if llm_provider:
            payload["llm_provider"] = llm_provider
        url = _v2_complete_url()

    response = requests.post(
        url,
        headers=_compress_headers(),
        json=payload,
        timeout=timeout,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:800]
        raise RuntimeError(f"Compress request failed: {exc}. Response body: {detail}") from exc

    body = response.json()
    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if content is None:
        message_payload = body.get("choices", [{}])[0].get("message", {})
        content = json.dumps(message_payload, ensure_ascii=False)

    text = str(content)
    if mode == "v2_complete":
        footer = _v2_meta_footer(body)
        if footer:
            text += footer

    return {"messages": [AIMessage(content=text)]}


workflow = StateGraph(MessagesState)
workflow.add_node("compress_chat", call_compress)
workflow.set_entry_point("compress_chat")
workflow.add_edge("compress_chat", END)
