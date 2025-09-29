from cat.mad_hatter.decorators import hook
import json

TOOLS_PATH = "cat/static/tools_status.json"
STATUS_PATH = "cat/static/user_status.json"



# ----------------------- helpers -----------------------

def _load_tools_status(path: str = TOOLS_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def get_enabled_tools (cat, path: str = TOOLS_PATH):
    ts = _load_tools_status()
    uid = str(getattr(cat, "user_id", "") or "")

    tools_cfg = ts.get("tools", {})
    enabled_tools = [
        tool_key
        for tool_key, cfg in tools_cfg.items()
        if bool(cfg.get("user_id_tool_status", {}).get(uid, False))
    ]
    
    if "Internet Search" in enabled_tools:
        enabled_tools.remove("Internet Search")
        enabled_tools.append("duck_duck_go_search")
        enabled_tools.append("crawl_site_content")

    if "Approfondisci documentazione" in enabled_tools:
        enabled_tools.remove("Approfondisci documentazione")
        enabled_tools.append("declarative_search")

#    cat.send_ws_message(str(enabled_tools),"chat")

    return enabled_tools

def _load_user_status(path: str = STATUS_PATH) -> dict:
    """Carica user_status.json in modo robusto."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def _get_selected_tag_for_user(uid: str, user_status: dict) -> str | None:
    """
    Restituisce il nome del primo tag con status=True per l'utente uid.
    Se non c'è alcun tag attivo, ritorna None.
    """
    tags_for_user = user_status.get(uid, {})
    if isinstance(tags_for_user, dict):
        for tag_name, tag_obj in tags_for_user.items():
            if isinstance(tag_obj, dict) and tag_obj.get("status", False):
                return tag_name
    return None

# ----------------------- hooks -----------------------

@hook  # default priority = 1
def agent_allowed_tools(allowed_tools, cat):
    enabled_tools = get_enabled_tools(cat)
    return enabled_tools

@hook(priority=5)
def agent_prompt_prefix(prefix, cat):
    """
    Compone una lista di capacità in base ai tool abilitati e
    inserisce il tag selezionato dall'utente (status=True) preso da user_status.json.
    """
    enabled_tools = get_enabled_tools(cat)
    lines = []

    if "duck_duck_go_search" in enabled_tools:
        lines.append(" - search on the internet with the tool 'duck_duck_go_search'")
    if "crawl_site_content" in enabled_tools:
        lines.append(" - read the content of a website with the tool 'crawl_site_content'")

    # Recupera il tag selezionato per l'utente corrente
    try:
        uid = str(getattr(cat, "user_id", "") or "")
        user_status = _load_user_status()
        selected_tag = _get_selected_tag_for_user(uid, user_status)
    except Exception:
        selected_tag = None

    if "declarative_search" in enabled_tools:
        tag_label = selected_tag or "<no tag selected>"
        lines.append(f" - analize '{tag_label}' documentation with the tool 'declarative_search'")

    you_are_able_to = "You are able to :"
    iterate ="""Iterate your actions until you find an exaustive answer to the user question.\n
## Behaviour instructions:"""
    resolved = (you_are_able_to+"\n" + "\n".join(lines)+"\n"+iterate) if lines else ""
    final_prefix = f"{prefix}{resolved}"
    return final_prefix
