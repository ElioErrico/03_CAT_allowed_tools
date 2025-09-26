from cat.mad_hatter.decorators import hook
import json

TOOLS_PATH = "cat/static/tools_status.json"

def _load_tools_status(path: str = TOOLS_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

@hook  # default priority = 1
def agent_allowed_tools(allowed_tools, cat):
    ts = _load_tools_status()
    uid = str(getattr(cat, "user_id", "") or "")

    tools_cfg = ts.get("tools", {})
    enabled_tools = [
        tool_key
        for tool_key, cfg in tools_cfg.items()
        if bool(cfg.get("user_id_tool_status", {}).get(uid, False))
    ]
    cat.send_ws_message(str(enabled_tools),"chat")
    return enabled_tools
