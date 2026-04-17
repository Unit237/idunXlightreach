#!/usr/bin/env sh
set -eu
cd /app

# Idun's `idun agent serve` calls `run_server(app, port=...)` without `host`.
# `run_server` defaults to host=localhost, which breaks Docker port publishing.
# See: idun_platform_cli/groups/agent/serve.py — run_server(app, port=..., reload=False)
exec python - <<'PY'
from idun_agent_engine.core.app_factory import create_app
from idun_agent_engine.core.config_builder import ConfigBuilder
from idun_agent_engine.core.server_runner import run_server

cfg = ConfigBuilder().load_from_file("config.yaml")
app = create_app(engine_config=cfg)
run_server(app, host="0.0.0.0", port=cfg.server.api.port, reload=False)
PY
