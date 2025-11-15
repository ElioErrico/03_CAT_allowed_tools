from cat.mad_hatter.decorators import hook
import json

TOOLS_PATH = "cat/static/tools_status.json"
STATUS_PATH = "cat/static/user_status.json"


# =====================================================================================
# GUIDA: COME AGGIUNGERE UN NUOVO TOOL
# =====================================================================================
#
# Per aggiungere un nuovo tool al sistema, segui questi passaggi:
#
# 1. AGGIUNGI IL CAMPO IN settings.py
#    - Vai in settings.py nella classe MySettings
#    - Aggiungi un nuovo campo con la descrizione del tool:
#      
#      new_tool_description: str = Field(
#          title="Nome Tool Description",
#          default=" - descrizione del nuovo tool\n",
#          extra={"type": "TextArea"},
#      )
#
# 2. AGGIUNGI IL MAPPING IN get_enabled_tools() (vedi sezione contrassegnata sotto)
#    - Se il tool ha un nome "user-friendly" diverso dal nome tecnico
#    - Aggiungi un blocco if per mappare il nome:
#      
#      if "Nome User Friendly" in enabled_tools:
#          enabled_tools.remove("Nome User Friendly")
#          enabled_tools.append("nome_tecnico_tool")
#
# 3. AGGIUNGI LA LOGICA NEL PROMPT in agent_prompt_prefix() (vedi sezione contrassegnata sotto)
#    - Aggiungi un blocco if per includere la descrizione quando il tool è abilitato:
#      
#      if "nome_tecnico_tool" in enabled_tools:
#          lines.append(settings["new_tool_description"])
#
# 4. SE IL TOOL USA PLACEHOLDER DINAMICI (come {tag_label})
#    - Usa .format() per sostituire i placeholder:
#      
#      tool_desc = settings["new_tool_description"].format(
#          placeholder=valore_dinamico
#      )
#      lines.append(tool_desc)
#
# =====================================================================================


# ----------------------- helpers -----------------------

def _load_tools_status(path: str = TOOLS_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def get_enabled_tools(cat, path: str = TOOLS_PATH):
    ts = _load_tools_status()
    uid = str(getattr(cat, "user_id", "") or "")

    tools_cfg = ts.get("tools", {})
    enabled_tools = [
        tool_key
        for tool_key, cfg in tools_cfg.items()
        if bool(cfg.get("user_id_tool_status", {}).get(uid, False))
    ]
    
    # ============== MAPPING TOOL: AGGIUNGI NUOVI TOOL QUI ==============
    # Se un tool ha un nome "user-friendly" che deve essere mappato
    # a uno o più tool tecnici, aggiungi il mapping qui sotto
    
    if "Internet Search" in enabled_tools:
        enabled_tools.remove("Internet Search")
        enabled_tools.append("duck_duck_go_search")
        enabled_tools.append("crawl_site_content")

    if "Approfondisci documentazione" in enabled_tools:
        enabled_tools.remove("Approfondisci documentazione")
        enabled_tools.append("declarative_search")
    
    if "Deep Think" in enabled_tools:
        enabled_tools.remove("Deep Think")
        enabled_tools.append("deep_think")

    if "Report Maker" in enabled_tools:
        enabled_tools.remove("Report Maker")
        enabled_tools.append("create_report_in_word")

    if "Plan and Execute" in enabled_tools:
        enabled_tools.remove("Plan and Execute")
        enabled_tools.append("plan_and_execute")

    # INSERISCI NUOVO TOOL MAPPING QUI
    # Esempio:
    # if "Nome User Friendly" in enabled_tools:
    #     enabled_tools.remove("Nome User Friendly")
    #     enabled_tools.append("nome_tecnico_tool")
    
    # ===================================================================

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
    # Carica settings dal plugin
    settings = cat.mad_hatter.get_plugin().load_settings()
    
    enabled_tools = get_enabled_tools(cat)
    lines = []

    # ============== DESCRIZIONI TOOL: AGGIUNGI NUOVI TOOL QUI ==============
    # Per ogni tool abilitato, aggiungi la sua descrizione al prompt
    # Le descrizioni vengono caricate dai settings
    
    # Usa le descrizioni dai settings
    if "duck_duck_go_search" in enabled_tools:
        lines.append(settings["duck_duck_go_search_description"])
    
    if "crawl_site_content" in enabled_tools:
        lines.append(settings["crawl_site_content_description"])

    # Recupera il tag selezionato per l'utente corrente
    try:
        uid = str(getattr(cat, "user_id", "") or "")
        user_status = _load_user_status()
        selected_tag = _get_selected_tag_for_user(uid, user_status)
    except Exception:
        selected_tag = None

    if "declarative_search" in enabled_tools:
        tag_label = selected_tag or "<no tag selected>"
        # Sostituisce {tag_label} nella descrizione dai settings
        declarative_desc = settings["declarative_search_description"].format(
            tag_label=tag_label
        )
        lines.append(declarative_desc)

    if "deep_think" in enabled_tools:
        lines.append(settings["deep_think_description"])

    if "create_report_in_word" in enabled_tools:
        lines.append(settings["create_report_in_word_description"])
    
    if "plan_and_execute" in enabled_tools:
        lines.append(settings["plan_and_execute_description"])
            
    # INSERISCI NUOVO TOOL DESCRIPTION QUI
    # Esempio base:
    # if "nome_tecnico_tool" in enabled_tools:
    #     lines.append(settings["new_tool_description"])
    #
    # Esempio con placeholder dinamici:
    # if "nome_tecnico_tool" in enabled_tools:
    #     tool_desc = settings["new_tool_description"].format(
    #         placeholder1=valore1,
    #         placeholder2=valore2
    #     )
    #     lines.append(tool_desc)
    
    # =======================================================================

    # Compone il prefix usando i prompt dai settings
    resolved = ""
    if lines:
        resolved = (
            settings["prompt_prefix_incipit"] +
            "\n" +
            settings["tool_orchestration_header"] +
            "\n" +
            "\n".join(lines) +
            "\n" +
            settings["metacognitive_practices"]+
            "\n" +
            settings["behaviour_practices"]
            
        )
    
    final_prefix = f"{prefix}{resolved}"
    return final_prefix
