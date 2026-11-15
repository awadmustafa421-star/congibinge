"""
db.py — Supabase Database Client & CRUD Operations.
Includes automatic expiry cleanup, multi-thread chat storage, memory cell reordering,
advisor configurations, and robust session-state fallback if secrets are pending.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import streamlit as st

# Optional Supabase import with safety check
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False
    Client = Any  # type: ignore


# ====================================================================
# SUPABASE CLIENT INITIALIZATION & STATUS
# ====================================================================

@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Optional[Client]:
    """
    Initializes and caches the Supabase client using Streamlit Secrets or Environment Variables.
    Returns None if credentials are not configured or connection fails.
    """
    if not HAS_SUPABASE_LIB:
        return None

    # Check secrets or environment
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        return None

    try:
        client: Client = create_client(str(url).strip(), str(key).strip())
        return client
    except Exception as e:
        print(f"[Supabase Init Error] {e}")
        return None


def is_supabase_connected() -> bool:
    """Checks if a valid Supabase client is active."""
    return get_supabase_client() is not None


# ====================================================================
# SESSION-STATE LOCAL STORAGE FALLBACK
# ====================================================================

def _init_local_db():
    """Seeds in-memory local state if Supabase credentials are not provided yet."""
    if "local_db" not in st.session_state:
        st.session_state["local_db"] = {
            "advisors": [
                {
                    "id": "adv-academic",
                    "name": "University Advisor",
                    "icon": "🎓",
                    "color": "#4E80EE",
                    "system_instructions": "You are my rigorous, supportive academic advisor. You prioritize conceptual mastery, precise problem-solving steps, structured unit reviews, and strategic study scheduling.",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "adv-architect",
                    "name": "Tech Architect",
                    "icon": "💻",
                    "color": "#34A853",
                    "system_instructions": "You are my senior cloud systems architect and software engineering advisor. You emphasize clean code, distributed architecture, scalability, security, and pragmatic trade-offs.",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "memory_cells": [
                {
                    "id": "mem-main-1",
                    "scope": "main",
                    "title": "🎯 Core Objective 2026",
                    "content": "Focusing on advanced distributed computing, AI agents, and maintaining high academic excellence. Prefer concise, high-signal explanations with code examples.",
                    "cell_order": 0,
                    "expires_at": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "mem-main-2",
                    "scope": "main",
                    "title": "⚙️ Engineering Standards",
                    "content": "Always adhere to clean architecture, explicit type hinting in Python, comprehensive documentation, and modern UI best practices.",
                    "cell_order": 1,
                    "expires_at": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "mem-adv-1",
                    "scope": "adv-academic",
                    "title": "📚 Semester Curriculum & Milestones",
                    "content": "Current focus: Advanced Database Systems (Supabase/PostgreSQL internals), Machine Learning Systems, and Distributed Consensus algorithms.",
                    "cell_order": 0,
                    "expires_at": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "chat_threads": [
                {
                    "id": "thread-main-default",
                    "scope": "main",
                    "title": "Welcome & Getting Started",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "chat_messages": [
                {
                    "id": "msg-welcome-1",
                    "thread_id": "thread-main-default",
                    "role": "assistant",
                    "content": "Hello! I am your **Personal AI Advisor & Memory Vault**, modeled after Google AI Studio.\n\nI retain persistent context across all your sessions and advisors using your Memory Vault cells. You can chat with me, switch between specialized Advisors, upload plain text files, or inspect my inner Thinking Process.\n\nHow can I help you today?",
                    "thinking_process": "Initialized Personal AI Advisor. Loaded shared main memory cells [Core Objective 2026, Engineering Standards]. Ready to assist with full context awareness.",
                    "search_html": None,
                    "sources_json": None,
                    "attached_file_name": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "app_settings": {
                "id": "default",
                "selected_model": "gemini-4-hydrogen",
                "enable_google_search": True,
                "enable_url_context": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        }


# ====================================================================
# AUTOMATIC EXPIRY CLEANUP
# ====================================================================

def cleanup_expired_memories() -> int:
    """
    Deletes memory cells whose expires_at is past the current UTC time.
    Returns the number of expired cells removed.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    client = get_supabase_client()

    if client:
        try:
            # Delete in Supabase where expires_at is not null and <= now
            res = client.table("memory_cells").delete().not_.is_("expires_at", "null").lte("expires_at", now_iso).execute()
            count = len(res.data) if res.data else 0
            return count
        except Exception as e:
            print(f"[Supabase Expiry Cleanup Error] {e}")

    # Fallback in local state
    _init_local_db()
    cells = st.session_state["local_db"]["memory_cells"]
    now = datetime.now(timezone.utc)
    retained = []
    removed_count = 0
    for cell in cells:
        exp = cell.get("expires_at")
        if exp:
            try:
                # Parse ISO timestamp
                exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                if exp_dt <= now:
                    removed_count += 1
                    continue
            except Exception:
                pass
        retained.append(cell)
    st.session_state["local_db"]["memory_cells"] = retained
    return removed_count


# ====================================================================
# MEMORY CELLS CRUD
# ====================================================================

def get_memories(scope: str = "main") -> List[Dict[str, Any]]:
    """
    Retrieves active (non-expired) memory cells for a given scope ('main' or advisor_id).
    Automatically runs cleanup_expired_memories first.
    """
    cleanup_expired_memories()
    client = get_supabase_client()

    if client:
        try:
            response = client.table("memory_cells") \
                .select("*") \
                .eq("scope", scope) \
                .order("cell_order", desc=False) \
                .order("created_at", desc=False) \
                .execute()
            if response.data is not None:
                return response.data
        except Exception as e:
            print(f"[Supabase get_memories error] {e}")

    # Local fallback
    _init_local_db()
    cells = [c for c in st.session_state["local_db"]["memory_cells"] if c.get("scope") == scope]
    cells.sort(key=lambda x: (x.get("cell_order", 0), x.get("created_at", "")))
    return cells


def create_memory_cell(
    scope: str,
    title: str,
    content: str,
    cell_order: Optional[int] = None,
    expires_at: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new memory cell in Supabase or local state."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    if cell_order is None:
        existing = get_memories(scope)
        cell_order = len(existing)

    cell_data = {
        "id": f"mem-{uuid.uuid4().hex[:12]}",
        "scope": scope,
        "title": title.strip() or "Untitled Memory",
        "content": content.strip(),
        "cell_order": cell_order,
        "expires_at": expires_at,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    if client:
        try:
            res = client.table("memory_cells").insert(cell_data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            print(f"[Supabase create_memory_cell error] {e}")

    _init_local_db()
    st.session_state["local_db"]["memory_cells"].append(cell_data)
    return cell_data


def update_memory_cell(
    cell_id: str,
    title: str,
    content: str,
    expires_at: Optional[str] = None
) -> bool:
    """Updates an existing memory cell."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    update_payload = {
        "title": title.strip(),
        "content": content.strip(),
        "expires_at": expires_at,
        "updated_at": now_iso,
    }

    if client:
        try:
            client.table("memory_cells").update(update_payload).eq("id", cell_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase update_memory_cell error] {e}")

    _init_local_db()
    for cell in st.session_state["local_db"]["memory_cells"]:
        if cell["id"] == cell_id:
            cell["title"] = update_payload["title"]
            cell["content"] = update_payload["content"]
            cell["expires_at"] = update_payload["expires_at"]
            cell["updated_at"] = update_payload["updated_at"]
            return True
    return False


def delete_memory_cell(cell_id: str) -> bool:
    """Deletes a memory cell by ID."""
    client = get_supabase_client()
    if client:
        try:
            client.table("memory_cells").delete().eq("id", cell_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase delete_memory_cell error] {e}")

    _init_local_db()
    st.session_state["local_db"]["memory_cells"] = [
        c for c in st.session_state["local_db"]["memory_cells"] if c["id"] != cell_id
    ]
    return True


def reorder_memory_cells(scope: str, ordered_cell_ids: List[str]) -> bool:
    """Updates the cell_order of all cells in a given scope."""
    client = get_supabase_client()
    if client:
        try:
            for idx, c_id in enumerate(ordered_cell_ids):
                client.table("memory_cells").update({"cell_order": idx}).eq("id", c_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase reorder_memory_cells error] {e}")

    _init_local_db()
    id_to_order = {c_id: idx for idx, c_id in enumerate(ordered_cell_ids)}
    for cell in st.session_state["local_db"]["memory_cells"]:
        if cell.get("scope") == scope and cell["id"] in id_to_order:
            cell["cell_order"] = id_to_order[cell["id"]]
    return True


# ====================================================================
# ADVISORS CRUD
# ====================================================================

def get_advisors() -> List[Dict[str, Any]]:
    """Retrieves all defined Advisors."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("advisors").select("*").order("created_at", desc=False).execute()
            if res.data is not None:
                return res.data
        except Exception as e:
            print(f"[Supabase get_advisors error] {e}")

    _init_local_db()
    return list(st.session_state["local_db"]["advisors"])


def get_advisor(advisor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single Advisor by ID."""
    for adv in get_advisors():
        if adv["id"] == advisor_id:
            return adv
    return None


def create_advisor(
    name: str,
    icon: str = "🤖",
    color: str = "#4E80EE",
    system_instructions: str = ""
) -> Dict[str, Any]:
    """Creates a new Advisor."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    adv_id = f"adv-{uuid.uuid4().hex[:8]}"

    payload = {
        "id": adv_id,
        "name": name.strip() or "Custom Advisor",
        "icon": icon.strip() or "🤖",
        "color": color or "#4E80EE",
        "system_instructions": system_instructions.strip(),
        "created_at": now_iso,
    }

    if client:
        try:
            res = client.table("advisors").insert(payload).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            print(f"[Supabase create_advisor error] {e}")

    _init_local_db()
    st.session_state["local_db"]["advisors"].append(payload)
    return payload


def update_advisor(
    advisor_id: str,
    name: str,
    icon: str,
    color: str,
    system_instructions: str
) -> bool:
    """Updates an existing Advisor."""
    client = get_supabase_client()
    payload = {
        "name": name.strip(),
        "icon": icon.strip(),
        "color": color,
        "system_instructions": system_instructions.strip(),
    }

    if client:
        try:
            client.table("advisors").update(payload).eq("id", advisor_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase update_advisor error] {e}")

    _init_local_db()
    for adv in st.session_state["local_db"]["advisors"]:
        if adv["id"] == advisor_id:
            adv.update(payload)
            return True
    return False


def delete_advisor(advisor_id: str) -> bool:
    """Deletes an Advisor, along with its isolated memories and threads."""
    client = get_supabase_client()
    if client:
        try:
            client.table("memory_cells").delete().eq("scope", advisor_id).execute()
            client.table("chat_threads").delete().eq("scope", advisor_id).execute()
            client.table("advisors").delete().eq("id", advisor_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase delete_advisor error] {e}")

    _init_local_db()
    st.session_state["local_db"]["advisors"] = [
        a for a in st.session_state["local_db"]["advisors"] if a["id"] != advisor_id
    ]
    st.session_state["local_db"]["memory_cells"] = [
        m for m in st.session_state["local_db"]["memory_cells"] if m.get("scope") != advisor_id
    ]
    st.session_state["local_db"]["chat_threads"] = [
        t for t in st.session_state["local_db"]["chat_threads"] if t.get("scope") != advisor_id
    ]
    return True


# ====================================================================
# CHAT THREADS CRUD
# ====================================================================

def get_threads(scope: str = "main") -> List[Dict[str, Any]]:
    """Retrieves all chat threads for a given scope ('main' or advisor_id)."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("chat_threads") \
                .select("*") \
                .eq("scope", scope) \
                .order("updated_at", desc=True) \
                .execute()
            if res.data is not None:
                return res.data
        except Exception as e:
            print(f"[Supabase get_threads error] {e}")

    _init_local_db()
    threads = [t for t in st.session_state["local_db"]["chat_threads"] if t.get("scope") == scope]
    threads.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return threads


def create_thread(scope: str = "main", title: str = "New Conversation") -> Dict[str, Any]:
    """Creates a new chat thread."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    t_id = f"thread-{uuid.uuid4().hex[:12]}"

    payload = {
        "id": t_id,
        "scope": scope,
        "title": title.strip() or "New Conversation",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    if client:
        try:
            res = client.table("chat_threads").insert(payload).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            print(f"[Supabase create_thread error] {e}")

    _init_local_db()
    st.session_state["local_db"]["chat_threads"].insert(0, payload)
    return payload


def update_thread_title(thread_id: str, title: str) -> bool:
    """Updates a chat thread's title."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {"title": title.strip(), "updated_at": now_iso}

    if client:
        try:
            client.table("chat_threads").update(payload).eq("id", thread_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase update_thread_title error] {e}")

    _init_local_db()
    for t in st.session_state["local_db"]["chat_threads"]:
        if t["id"] == thread_id:
            t["title"] = payload["title"]
            t["updated_at"] = payload["updated_at"]
            return True
    return False


def touch_thread(thread_id: str):
    """Bumps thread updated_at to bring it to the top."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    if client:
        try:
            client.table("chat_threads").update({"updated_at": now_iso}).eq("id", thread_id).execute()
        except Exception:
            pass

    _init_local_db()
    for t in st.session_state["local_db"]["chat_threads"]:
        if t["id"] == thread_id:
            t["updated_at"] = now_iso


def delete_thread(thread_id: str) -> bool:
    """Deletes a chat thread and all its messages."""
    client = get_supabase_client()
    if client:
        try:
            client.table("chat_threads").delete().eq("id", thread_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase delete_thread error] {e}")

    _init_local_db()
    st.session_state["local_db"]["chat_threads"] = [
        t for t in st.session_state["local_db"]["chat_threads"] if t["id"] != thread_id
    ]
    st.session_state["local_db"]["chat_messages"] = [
        m for m in st.session_state["local_db"]["chat_messages"] if m.get("thread_id") != thread_id
    ]
    return True


# ====================================================================
# CHAT MESSAGES CRUD
# ====================================================================

def get_messages(thread_id: str) -> List[Dict[str, Any]]:
    """Retrieves all messages for a specific chat thread in chronological order."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("chat_messages") \
                .select("*") \
                .eq("thread_id", thread_id) \
                .order("created_at", desc=False) \
                .execute()
            if res.data is not None:
                return res.data
        except Exception as e:
            print(f"[Supabase get_messages error] {e}")

    _init_local_db()
    msgs = [m for m in st.session_state["local_db"]["chat_messages"] if m.get("thread_id") == thread_id]
    msgs.sort(key=lambda x: x.get("created_at", ""))
    return msgs


def add_message(
    thread_id: str,
    role: str,
    content: str,
    thinking_process: Optional[str] = None,
    search_html: Optional[str] = None,
    sources_json: Optional[Any] = None,
    attached_file_name: Optional[str] = None
) -> Dict[str, Any]:
    """Adds a message to a thread and touches the thread's updated_at."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    msg_id = f"msg-{uuid.uuid4().hex[:12]}"

    payload = {
        "id": msg_id,
        "thread_id": thread_id,
        "role": role,
        "content": content,
        "thinking_process": thinking_process,
        "search_html": search_html,
        "sources_json": sources_json,
        "attached_file_name": attached_file_name,
        "created_at": now_iso,
    }

    if client:
        try:
            res = client.table("chat_messages").insert(payload).execute()
            touch_thread(thread_id)
            if res.data:
                return res.data[0]
        except Exception as e:
            print(f"[Supabase add_message error] {e}")

    _init_local_db()
    st.session_state["local_db"]["chat_messages"].append(payload)
    touch_thread(thread_id)
    return payload


# ====================================================================
# APP SETTINGS CRUD
# ====================================================================

def get_settings() -> Dict[str, Any]:
    """Retrieves application settings."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("app_settings").select("*").eq("id", "default").execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            print(f"[Supabase get_settings error] {e}")

    _init_local_db()
    return dict(st.session_state["local_db"]["app_settings"])


def update_settings(
    selected_model: str,
    enable_google_search: bool,
    enable_url_context: bool
) -> bool:
    """Updates application settings."""
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "id": "default",
        "selected_model": selected_model,
        "enable_google_search": enable_google_search,
        "enable_url_context": enable_url_context,
        "updated_at": now_iso,
    }

    if client:
        try:
            client.table("app_settings").upsert(payload).execute()
            return True
        except Exception as e:
            print(f"[Supabase update_settings error] {e}")

    _init_local_db()
    st.session_state["local_db"]["app_settings"] = payload
    return True
