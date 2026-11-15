"""
ai_engine.py — Official google-genai SDK Wrapper.
Features multi-API-key rotation/failover, thinking extraction, Search Grounding,
URL context, and post-response Memory Proposal analyzer.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st

# Official google-genai SDK imports with graceful handling
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False
    genai = None  # type: ignore
    types = None  # type: ignore
    APIError = Exception  # type: ignore


# ====================================================================
# MULTI-API-KEY ROTATION & POOL MANAGEMENT
# ====================================================================

def get_api_key_pool() -> List[str]:
    """
    Retrieves the list of Gemini API keys configured in Streamlit Secrets,
    environment variables, or session state.
    Supports either a list of strings or a comma/newline-delimited string.
    """
    keys: List[str] = []

    # 1. Check Streamlit Secrets
    if "GEMINI_API_KEYS" in st.secrets:
        raw = st.secrets["GEMINI_API_KEYS"]
        if isinstance(raw, list):
            keys.extend([str(k).strip() for k in raw if str(k).strip()])
        elif isinstance(raw, str):
            for part in raw.replace("\n", ",").split(","):
                if part.strip():
                    keys.append(part.strip())

    # 2. Check single GEMINI_API_KEY secret or env var
    if not keys:
        single_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if single_key:
            keys.append(str(single_key).strip())

    # 3. Check Session State overrides from Settings page
    if "custom_api_keys" in st.session_state and st.session_state["custom_api_keys"]:
        custom_list = st.session_state["custom_api_keys"]
        if isinstance(custom_list, list):
            for k in custom_list:
                k_clean = str(k).strip()
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)

    return keys


def get_key_status_overview() -> List[Dict[str, Any]]:
    """Returns masked status diagnostics for each configured API key."""
    keys = get_api_key_pool()
    current_idx = st.session_state.get("api_key_index", 0)
    key_states = st.session_state.get("key_health_status", {})

    overview = []
    for idx, key in enumerate(keys):
        masked = f"Key {idx + 1} ••••{key[-4:]}" if len(key) >= 6 else f"Key {idx + 1} (short)"
        status = key_states.get(key, "Ready")
        is_active = (idx == (current_idx % len(keys))) if keys else False
        overview.append({
            "index": idx,
            "masked": masked,
            "status": status,
            "is_active": is_active,
        })
    return overview


def get_next_client() -> Tuple[Any, str, int]:
    """
    Returns (client, active_key, key_index) from the rotated key pool.
    Increments rotation pointer in round-robin fashion.
    """
    if not HAS_GENAI_SDK:
        raise RuntimeError("The 'google-genai' SDK is not installed. Please install requirements.txt.")

    keys = get_api_key_pool()
    if not keys:
        raise ValueError(
            "No Gemini API keys found. Please configure GEMINI_API_KEYS in .streamlit/secrets.toml "
            "or enter keys on the Settings page."
        )

    current_idx = st.session_state.get("api_key_index", 0) % len(keys)
    active_key = keys[current_idx]
    
    # Advance pointer for next request
    st.session_state["api_key_index"] = (current_idx + 1) % len(keys)

    client = genai.Client(api_key=active_key)
    return client, active_key, current_idx


def mark_key_status(key: str, status: str):
    """Updates key health status in session state."""
    if "key_health_status" not in st.session_state:
        st.session_state["key_health_status"] = {}
    st.session_state["key_health_status"][key] = status


# ====================================================================
# PROMPT CONTEXT ASSEMBLY WITH MEMORY CELLS
# ====================================================================

def build_system_instruction(
    scope: str,
    advisor: Optional[Dict[str, Any]],
    shared_memories: List[Dict[str, Any]],
    advisor_memories: List[Dict[str, Any]]
) -> str:
    """
    Builds the rich system prompt integrating:
    - Base Advisor/Personal Assistant persona
    - 100% of active shared Main Memory Cells
    - 100% of active isolated Advisor Memory Cells (if in advisor scope)
    - Precise Current Date/Time in UTC
    """
    now_utc = datetime.now(timezone.utc).strftime("%A, %B %d, %Y at %H:%M:%S UTC")

    # Base Persona
    if advisor:
        advisor_name = advisor.get("name", "Specialized Advisor")
        custom_instructions = advisor.get("system_instructions", "")
        persona_header = f"""
You are {advisor_name}, an elite AI advisor operating within the user's Personal AI Advisor & Memory Vault (Google AI Studio aesthetic).
Your primary role and custom instructions are:
\"\"\"{custom_instructions}\"\"\"
"""
    else:
        persona_header = """
You are the user's Personal AI Advisor & Memory Vault, modeled after Google AI Studio.
You act as a deeply knowledgeable, rigorous, concise, and structured personal intellectual partner.
You retain active contextual memory across turns, synthesize complex ideas cleanly, and prioritize actionable clarity.
"""

    # Assemble Main Shared Memories
    shared_text = ""
    if shared_memories:
        lines = []
        for idx, m in enumerate(shared_memories, 1):
            exp_info = f" [Expires: {m['expires_at']}]" if m.get("expires_at") else " [Permanent]"
            lines.append(f"Cell #{idx} - {m.get('title', 'Untitled')}{exp_info}:\n{m.get('content', '')}")
        shared_text = "\n\n".join(lines)
    else:
        shared_text = "None currently stored."

    # Assemble Advisor Isolated Memories
    advisor_text = ""
    if advisor and advisor_memories:
        lines = []
        for idx, m in enumerate(advisor_memories, 1):
            exp_info = f" [Expires: {m['expires_at']}]" if m.get("expires_at") else " [Permanent]"
            lines.append(f"Advisor Cell #{idx} - {m.get('title', 'Untitled')}{exp_info}:\n{m.get('content', '')}")
        advisor_text = "\n\n".join(lines)
    elif advisor:
        advisor_text = "None currently stored for this advisor."

    system_instruction = f"""
{persona_header}

CURRENT CALENDAR TIMESTAMP: {now_utc}
(Use this precise timestamp to understand relative dates such as 'today', 'tomorrow', 'next week', 'in 3 days', or active memory expiry deadlines.)

====================================================================
ACTIVE MEMORY VAULT CELLS (Strict 100% active context retention):
====================================================================
--- SHARED MAIN MEMORY (Accessible everywhere) ---
{shared_text}
"""

    if advisor:
        system_instruction += f"""
--- ISOLATED ADVISOR MEMORY ({advisor.get('name', 'Advisor')}) ---
{advisor_text}
"""

    system_instruction += """
====================================================================
INTERACTION GUIDELINES:
1. Always incorporate relevant active Memory Vault cells into your reasoning.
2. If the user mentions temporary plans or time-sensitive events (e.g. 'dad buying headphones next week'), take note of the timeline.
3. Be direct, authoritative, structured, and helpful. Use clean Markdown formatting with clear headers, bullet points, and code blocks where applicable.
"""
    return system_instruction.strip()


# ====================================================================
# MAIN GENERATION ENGINE (THINKING + SEARCH + FAILOVER)
# ====================================================================

def generate_ai_response(
    messages: List[Dict[str, Any]],
    system_instruction: str,
    selected_model: str = "gemini-4-hydrogen",
    enable_google_search: bool = True,
    enable_url_context: bool = True,
    attachment_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a chat generation turn with multi-API-key failover:
    - Extracts thinking process (`part.thought`)
    - Collects final answer
    - Parses Google Search Grounding & citations
    """
    keys = get_api_key_pool()
    if not keys or not HAS_GENAI_SDK:
        # Graceful simulation fallback for testing if no keys are available
        return _fallback_simulated_response(messages, system_instruction, attachment_text)

    # Format history into types.Content
    contents = []
    for msg in messages:
        role = "user" if msg.get("role") == "user" else "model"
        text_content = msg.get("content", "")
        
        # If there's an attached plain text file on a user message
        if msg.get("attached_file_name") and msg.get("role") == "user":
            file_badge = f"\n\n[Attached File: {msg.get('attached_file_name')}]\n"
            text_content = f"{text_content}{file_badge}"
            
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text_content)]
            )
        )

    # If an attachment is provided for the current active turn
    if attachment_text and contents:
        last_turn = contents[-1]
        last_turn.parts.append(
            types.Part.from_text(text=f"\n\n--- UPLOADED FILE CONTEXT ---\n{attachment_text}\n--- END FILE CONTEXT ---\n")
        )

    # Configure tools
    tools = []
    if enable_google_search:
        tools.append(types.Tool(google_search=types.GoogleSearch()))
    if enable_url_context:
        tools.append(types.Tool(url_context=types.UrlContext()))

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        thinking_config=types.ThinkingConfig(include_thoughts=True),
        tools=tools if tools else None,
        # Temperature is kept unset / default for Gemini 3+/4 models per Google recommendation
    )

    # Failover loop across all available keys
    max_attempts = max(len(keys), 1)
    last_error = None

    for attempt in range(max_attempts):
        try:
            client, active_key, key_idx = get_next_client()
            mark_key_status(active_key, "Active")

            response = client.models.generate_content(
                model=selected_model,
                contents=contents,
                config=config,
            )

            # Mark key ready
            mark_key_status(active_key, "Ready")

            # Parse response parts
            thinking_parts = []
            answer_parts = []

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        # Extract thought
                        is_thought = getattr(part, "thought", False)
                        part_text = getattr(part, "text", "") or ""
                        if is_thought:
                            thinking_parts.append(part_text)
                        elif part_text:
                            answer_parts.append(part_text)

                # Grounding metadata
                search_html = None
                sources = []
                grounding_meta = getattr(candidate, "grounding_metadata", None)
                if grounding_meta:
                    # Search entry point rendered content
                    entry_point = getattr(grounding_meta, "search_entry_point", None)
                    if entry_point and hasattr(entry_point, "rendered_content"):
                        search_html = entry_point.rendered_content

                    # Grounding chunks (sources)
                    chunks = getattr(grounding_meta, "grounding_chunks", []) or []
                    for ch in chunks:
                        web = getattr(ch, "web", None)
                        if web:
                            sources.append({
                                "title": getattr(web, "title", "Web Source"),
                                "uri": getattr(web, "uri", "#")
                            })

                final_answer = "".join(answer_parts).strip()
                thinking_process = "\n".join(thinking_parts).strip() or None

                return {
                    "answer": final_answer or "(Empty response returned)",
                    "thinking_process": thinking_process,
                    "search_html": search_html,
                    "sources_json": sources if sources else None,
                    "model_used": selected_model,
                    "key_used": f"Key {key_idx + 1}",
                }

        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            print(f"[AI Generation Attempt {attempt + 1} Failed] {e}")
            if "quota" in err_str or "429" in err_str or "resource_exhausted" in err_str:
                mark_key_status(active_key, "Rate-Limited")
            else:
                mark_key_status(active_key, f"Error: {type(e).__name__}")
            continue

    # If all keys failed, surface error
    raise RuntimeError(f"All configured Gemini API keys failed. Last error: {last_error}")


# ====================================================================
# SMART MEMORY PROPOSAL ANALYZER
# ====================================================================

def analyze_for_memory_proposal(
    user_message: str,
    assistant_message: str,
    existing_memories: List[Dict[str, Any]],
    scope: str = "main"
) -> Optional[Dict[str, Any]]:
    """
    Evaluates whether the interaction contains valuable persistent context:
    - User personal details, long-term goals, preferences
    - Academic curriculum / study plans / unit review maps
    - Upcoming events with time-sensitive deadlines (e.g., 'dad buying headphones next week')
    Returns: { "should_save": bool, "title": str, "content": str, "suggested_expiry_days": int | None }
    """
    keys = get_api_key_pool()
    if not keys or not HAS_GENAI_SDK:
        return _fallback_memory_proposal(user_message, assistant_message)

    # Format existing memory titles to avoid redundant proposals
    existing_titles = [m.get("title", "") for m in existing_memories]

    eval_prompt = f"""
You are the Smart Memory Vault Proposal Analyzer for a Personal AI Advisor system.
Analyze the latest exchange between the User and the Assistant:

USER MESSAGE:
\"\"\"{user_message}\"\"\"

ASSISTANT RESPONSE:
\"\"\"{assistant_message[:1500]}\"\"\"

EXISTING MEMORY CELLS IN THIS SCOPE:
{json.dumps(existing_titles, indent=2)}

TASK:
Determine if there is a concrete, valuable piece of persistent information worth saving into the user's Memory Vault.
Worth saving includes:
1. Personal facts, hardware/device context, or recurring preferences (e.g. "My dad is buying me Sony headphones next week", "I prefer clean TypeScript with strict typing").
2. Educational study plans, curriculum breakdowns, or Unit Review Maps produced in the response.
3. Specific upcoming goals or deadlines.

DO NOT SAVE:
- Casual chit-chat, greetings ("hello", "thanks", "ok").
- Generic Q&A that is already well known or already saved in existing memory cells.

If time-sensitive (e.g. "next week", "in 3 days", "exam on Friday"), estimate `suggested_expiry_days` (an integer, e.g. 7, 10, 14, 30).
If it is a permanent preference, goal, or review note, set `suggested_expiry_days` to null.

Output STRICT JSON in this exact structure:
{{
  "should_save": true or false,
  "title": "Concise Emoji + Title (e.g. 🎧 Dad buying headphones)",
  "content": "Clear, standalone summary of the fact or review note.",
  "suggested_expiry_days": 10 or null
}}
"""

    try:
        client, _, _ = get_next_client()
        # Use gemini-3.5-flash-lite for ultra-fast, cheap evaluation
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=eval_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        text = response.text.strip()
        data = json.loads(text)
        if data.get("should_save"):
            return {
                "title": data.get("title", "New Memory Note"),
                "content": data.get("content", ""),
                "suggested_expiry_days": data.get("suggested_expiry_days"),
            }
        return None
    except Exception as e:
        print(f"[Memory Proposal Analyzer Error] {e}")
        return None


# ====================================================================
# SIMULATION / FALLBACK HANDLERS (When API Keys are missing)
# ====================================================================

def _fallback_simulated_response(
    messages: List[Dict[str, Any]],
    system_instruction: str,
    attachment_text: Optional[str]
) -> Dict[str, Any]:
    """Generates an informative simulated response for UI preview when keys are pending."""
    last_user_msg = messages[-1].get("content", "") if messages else "Hello"
    
    thought = (
        "1. Checked Gemini API key configuration: No active API key found in secrets or session.\n"
        "2. Operating in local preview mode.\n"
        "3. Evaluated system instruction and loaded memory context.\n"
        "4. Formulating guidance on setting up GEMINI_API_KEYS."
    )

    answer = f"""### ⚠️ Gemini API Key Required for Live Generation

You asked: **"{last_user_msg}"**

To activate live AI generation with **Thinking Process**, **Google Search Grounding**, and **Memory Proposals**:
1. Open the **`⚙️ Settings`** page from the top-right navigation bar.
2. Enter your Gemini API key in the temporary session input, or add `GEMINI_API_KEYS = ["AIzaSy..."]` into your `.streamlit/secrets.toml`.
3. Once configured, you can query **`gemini-4-hydrogen`**, inspect real-time thinking processes, and automate your Personal Memory Vault!
"""

    return {
        "answer": answer,
        "thinking_process": thought,
        "search_html": None,
        "sources_json": None,
        "model_used": "preview-mode",
        "key_used": "None",
    }


def _fallback_memory_proposal(user_message: str, assistant_message: str) -> Optional[Dict[str, Any]]:
    """Heuristic fallback for demoing memory proposal when SDK is offline."""
    user_lower = user_message.lower()
    if any(k in user_lower for k in ["dad is buying", "buying me", "next week", "exam", "deadline", "preference"]):
        return {
            "title": "📌 Noted Preference / Event",
            "content": f"User mentioned: {user_message.strip()}",
            "suggested_expiry_days": 10 if "next week" in user_lower else None,
        }
    return None
