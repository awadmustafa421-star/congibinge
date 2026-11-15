"""
app.py — Main Entry Point, Navigation Routing, and Core Workspaces.
Google AI Studio aesthetic: Permanent Dark Mode, rounded ergonomics, Colab-style memory vault,
multi-thread chats with plain text file ingestion, and multi-API-key failover.
"""

from datetime import datetime, timezone, timedelta, date
from typing import Optional, Dict, Any, List
import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="Personal AI Advisor & Memory Vault",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import internal modules
import styles
import db
import ai_engine
import ui_components

# Inject Google AI Studio permanent dark theme & rounded ergonomics CSS
st.markdown(styles.DARK_THEME_CSS, unsafe_allow_html=True)


# ====================================================================
# SESSION STATE INITIALIZATION
# ====================================================================

def init_session_state():
    """Initializes persistent application session state variables."""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "main_chat"

    if "selected_advisor_id" not in st.session_state:
        st.session_state["selected_advisor_id"] = None

    if "active_thread_id" not in st.session_state:
        st.session_state["active_thread_id"] = None

    if "pending_memory_proposal" not in st.session_state:
        st.session_state["pending_memory_proposal"] = None

    if "manual_pin_message" not in st.session_state:
        st.session_state["manual_pin_message"] = None

    if "custom_api_keys" not in st.session_state:
        st.session_state["custom_api_keys"] = []

    if "api_key_index" not in st.session_state:
        st.session_state["api_key_index"] = 0

    if "key_health_status" not in st.session_state:
        st.session_state["key_health_status"] = {}

    # Vault active sub-tab
    if "vault_scope" not in st.session_state:
        st.session_state["vault_scope"] = "main"


init_session_state()


# Navigation handler
def navigate_to(page: str, advisor_id: Optional[str] = None):
    st.session_state["current_page"] = page
    if advisor_id is not None:
        st.session_state["selected_advisor_id"] = advisor_id
    st.session_state["pending_memory_proposal"] = None
    st.session_state["manual_pin_message"] = None
    st.rerun()


# Top navigation bar
ui_components.render_top_navbar(
    current_page=st.session_state["current_page"],
    on_navigate=lambda p: navigate_to(p)
)

# Global notice if Supabase is in local demo/fallback mode
if not db.is_supabase_connected():
    st.info(
        "💡 **Notice:** Supabase is running in **local session mode**. Add `SUPABASE_URL` and `SUPABASE_KEY` "
        "to `.streamlit/secrets.toml` or Streamlit Cloud Secrets for persistent cloud database storage.",
        icon="ℹ️"
    )


# ====================================================================
# VIEW 1: CHAT WORKSPACE (MAIN CHAT & ADVISOR CHAT)
# ====================================================================

def render_chat_workspace(scope: str = "main", advisor: Optional[Dict[str, Any]] = None):
    """
    Renders the unified chat workspace for either Main Chat (scope='main')
    or a dedicated Advisor (scope=advisor_id).
    """
    # Ensure active thread exists for this scope
    threads = db.get_threads(scope=scope)
    if not threads:
        new_th = db.create_thread(scope=scope, title="New Conversation")
        st.session_state["active_thread_id"] = new_th["id"]
        active_thread_id = new_th["id"]
    else:
        # Check if current active thread belongs to this scope
        active_thread_id = st.session_state.get("active_thread_id")
        if not active_thread_id or not any(t["id"] == active_thread_id for t in threads):
            active_thread_id = threads[0]["id"]
            st.session_state["active_thread_id"] = active_thread_id

    # Sidebar: Saved Threads Drawer
    with st.sidebar:
        # Advisor Header if in advisor scope
        if advisor:
            adv_color = advisor.get("color", "#4E80EE")
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, {adv_color}22 0%, #171A23 100%); border: 1px solid {adv_color}55; border-radius: 18px; padding: 1rem; margin-bottom: 1.25rem; text-align: center;">
                    <div style="font-size: 2.2rem; margin-bottom: 0.25rem;">{advisor.get('icon', '🤖')}</div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 1.05rem;">{advisor.get('name', 'Advisor')}</div>
                    <div style="font-size: 0.8rem; color: #9AA0A6; margin-top: 0.35rem; line-height: 1.4;">{advisor.get('system_instructions', '')[:90]}...</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background: #171A23; border: 1px solid #2A303C; border-radius: 18px; padding: 1rem; margin-bottom: 1.25rem; text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.25rem;">🧠</div>
                    <div style="font-weight: 700; color: #F0F3F8; font-size: 1.05rem;">Main Personal Chat</div>
                    <div style="font-size: 0.8rem; color: #9AA0A6; margin-top: 0.25rem;">Powered by 100% Active Shared Memory</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Thread selector drawer
        ui_components.render_thread_selector(
            scope=scope,
            active_thread_id=active_thread_id,
            on_select_thread=lambda t_id: st.session_state.update({"active_thread_id": t_id}),
            on_new_thread=lambda: db.create_thread(scope=scope, title="New Conversation"),
            on_rename_thread=lambda t_id, title: db.update_thread_title(t_id, title),
            on_delete_thread=lambda t_id: db.delete_thread(t_id),
        )

        st.markdown("---")

        # Plain Text File Upload widget
        st.markdown("<div style='font-weight: 600; font-size: 0.85rem; color: #8AB4F8; margin-bottom: 0.35rem;'>📎 Attach Text Context</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Plain Text (.txt, .md, .csv, .json, .py, .log)",
            type=["txt", "md", "csv", "json", "py", "log", "yaml", "yml", "sql", "toml"],
            key=f"uploader_{active_thread_id}",
            help="Plain text files only to keep storage and token usage lightweight."
        )

    # Main Chat Feed
    messages = db.get_messages(active_thread_id)

    # Render message history
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        msg_id = msg.get("id")

        if role == "user":
            with st.container():
                st.markdown('<div class="chat-bubble-user">', unsafe_allow_html=True)
                ui_components.render_file_attachment_pill(msg.get("attached_file_name"))
                st.markdown(content)
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            with st.container():
                st.markdown('<div class="chat-bubble-assistant">', unsafe_allow_html=True)
                
                # 1. Thinking Process Bar
                ui_components.render_thinking_process(msg.get("thinking_process"))
                
                # 2. Final Answer
                st.markdown(content)
                
                # 3. Google Search Grounding & Sources
                ui_components.render_grounding_results(
                    search_html=msg.get("search_html"),
                    sources=msg.get("sources_json")
                )

                # 4. Manual Pin Button (Save to Memory)
                st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
                col_pin, _ = st.columns([2.5, 7.5])
                with col_pin:
                    if st.button("📌 Save to Memory", key=f"btn_pin_{msg_id}", help="Turn this answer into a Memory Cell"):
                        st.session_state["manual_pin_message"] = msg
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

    # Render Manual Pin Card if active
    if st.session_state.get("manual_pin_message"):
        advisors_list = db.get_advisors()
        ui_components.render_manual_pin_card(
            message=st.session_state["manual_pin_message"],
            default_scope=scope,
            advisors=advisors_list,
            on_save=lambda target_scope, title, body, exp: _handle_manual_pin(target_scope, title, body, exp),
            on_cancel=lambda: _dismiss_manual_pin()
        )

    # Render Smart Memory Proposal Card if pending
    if st.session_state.get("pending_memory_proposal"):
        proposal = st.session_state["pending_memory_proposal"]
        scope_name = "Main Shared" if scope == "main" else (advisor.get("name") if advisor else "Advisor")
        ui_components.render_memory_proposal_card(
            proposal=proposal,
            scope_name=scope_name,
            on_save=lambda title, body, exp: _save_proposed_memory(scope, title, body, exp),
            on_ignore=lambda: _dismiss_proposed_memory()
        )

    # Chat Input Box
    chat_prompt = st.chat_input(
        f"Message {advisor.get('name') if advisor else 'Personal Advisor'}..."
    )

    if chat_prompt:
        _handle_user_turn(
            user_text=chat_prompt,
            active_thread_id=active_thread_id,
            scope=scope,
            advisor=advisor,
            uploaded_file=uploaded_file
        )


def _handle_user_turn(
    user_text: str,
    active_thread_id: str,
    scope: str,
    advisor: Optional[Dict[str, Any]],
    uploaded_file: Optional[Any]
):
    """Processes user submission, invokes AI Engine with failover, and evaluates Memory Proposal."""
    # Read attachment if provided
    file_name = None
    attachment_text = None
    if uploaded_file is not None:
        try:
            file_name = uploaded_file.name
            attachment_text = uploaded_file.getvalue().decode("utf-8", errors="replace")
        except Exception as e:
            st.error(f"Failed to read uploaded file: {e}")

    # Auto-title thread if it's the first message
    existing_msgs = db.get_messages(active_thread_id)
    if len(existing_msgs) <= 1:
        # Generate snappy 5-8 word title
        words = user_text.strip().split()
        snappy_title = " ".join(words[:6]) + ("..." if len(words) > 6 else "")
        db.update_thread_title(active_thread_id, snappy_title)

    # 1. Save user message to database
    db.add_message(
        thread_id=active_thread_id,
        role="user",
        content=user_text,
        attached_file_name=file_name
    )

    # 2. Gather active Memory Vault cells (100% active context)
    shared_memories = db.get_memories("main")
    advisor_memories = db.get_memories(scope) if (scope != "main") else []

    # 3. Build system instruction
    system_instruction = ai_engine.build_system_instruction(
        scope=scope,
        advisor=advisor,
        shared_memories=shared_memories,
        advisor_memories=advisor_memories
    )

    # 4. Load full message history for active thread
    thread_history = db.get_messages(active_thread_id)

    # 5. Fetch app settings
    settings = db.get_settings()
    model = settings.get("selected_model", "gemini-4-hydrogen")
    enable_search = settings.get("enable_google_search", True)
    enable_url = settings.get("enable_url_context", True)

    # 6. Generate AI response with spinner
    with st.spinner("💭 Advisor is thinking & consulting Memory Vault..."):
        try:
            ai_res = ai_engine.generate_ai_response(
                messages=thread_history,
                system_instruction=system_instruction,
                selected_model=model,
                enable_google_search=enable_search,
                enable_url_context=enable_url,
                attachment_text=attachment_text
            )
        except Exception as e:
            st.error(f"Generation error: {e}")
            return

    # 7. Save assistant message to database
    db.add_message(
        thread_id=active_thread_id,
        role="assistant",
        content=ai_res["answer"],
        thinking_process=ai_res["thinking_process"],
        search_html=ai_res["search_html"],
        sources_json=ai_res["sources_json"]
    )

    # 8. Run lightweight background check for Smart Memory Proposal
    all_active_memories = shared_memories + advisor_memories
    proposal = ai_engine.analyze_for_memory_proposal(
        user_message=user_text,
        assistant_message=ai_res["answer"],
        existing_memories=all_active_memories,
        scope=scope
    )

    if proposal:
        st.session_state["pending_memory_proposal"] = proposal

    st.rerun()


def _save_proposed_memory(scope: str, title: str, content: str, expires_at: Optional[str]):
    """Commits an accepted AI memory proposal to Supabase."""
    db.create_memory_cell(
        scope=scope,
        title=title,
        content=content,
        expires_at=expires_at
    )
    st.session_state["pending_memory_proposal"] = None
    st.success("✅ Memory Cell committed to Vault!", icon="🧠")
    st.rerun()


def _dismiss_proposed_memory():
    st.session_state["pending_memory_proposal"] = None
    st.rerun()


def _handle_manual_pin(target_scope: str, title: str, content: str, expires_at: Optional[str]):
    """Commits a manually pinned response to the Memory Vault."""
    db.create_memory_cell(
        scope=target_scope,
        title=title,
        content=content,
        expires_at=expires_at
    )
    st.session_state["manual_pin_message"] = None
    st.success(f"📌 Pinned to {target_scope} vault!", icon="✅")
    st.rerun()


def _dismiss_manual_pin():
    st.session_state["manual_pin_message"] = None
    st.rerun()


# ====================================================================
# VIEW 2: MEMORY VAULT PAGE (GOOGLE COLAB CELL UX)
# ====================================================================

def render_memory_vault_view():
    """
    Renders the Google Colab-style Memory Vault:
    - Left sidebar separating Main Memory (Shared) and Each Advisor's Memory (Isolated)
    - Colab-style cells with badges [1], Move Up/Down, Edit, Expiry selector, Delete
    - + Add Cell buttons
    - Strict 100% active context rule (no mute toggle)
    """
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-weight: 700; color: #F0F3F8; margin-bottom: 0.25rem;">
                🧠 Memory Vault
            </h2>
            <p style="color: #9AA0A6; font-size: 0.95rem;">
                Persistent context modeled as Google Colab cells. The AI thinks using <strong>100% of active (non-expired) cells</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    advisors = db.get_advisors()

    # Left sidebar inside Memory Vault to toggle scope
    with st.sidebar:
        st.markdown("<div style='font-weight: 700; font-size: 0.9rem; color: #8AB4F8; margin-bottom: 0.75rem;'>VAULT SCOPES</div>", unsafe_allow_html=True)
        
        # Scope selection buttons
        is_main = (st.session_state["vault_scope"] == "main")
        if st.button("🌐 Main Shared Memory", key="vault_scope_main", type="primary" if is_main else "secondary", use_container_width=True):
            st.session_state["vault_scope"] = "main"
            st.rerun()

        st.markdown("<div style='font-size: 0.78rem; text-transform: uppercase; font-weight: 600; color: #6E7681; margin: 1rem 0 0.5rem 0;'>Advisor Isolated Memories</div>", unsafe_allow_html=True)
        for adv in advisors:
            adv_id = adv["id"]
            is_adv_active = (st.session_state["vault_scope"] == adv_id)
            if st.button(
                f"{adv.get('icon', '🤖')} {adv.get('name')}",
                key=f"v_scope_{adv_id}",
                type="primary" if is_adv_active else "secondary",
                use_container_width=True
            ):
                st.session_state["vault_scope"] = adv_id
                st.rerun()

    current_scope = st.session_state["vault_scope"]
    active_advisor = next((a for a in advisors if a["id"] == current_scope), None)

    # Vault Header Info
    if current_scope == "main":
        scope_title = "🌐 Main Shared Memory Vault"
        scope_desc = "These cells are loaded across the Main Chat AND every Advisor automatically."
    else:
        adv_name = active_advisor.get("name", "Advisor") if active_advisor else "Advisor"
        scope_title = f"{active_advisor.get('icon', '🤖')} {adv_name} (Isolated Vault)"
        scope_desc = f"These cells are isolated exclusively to {adv_name} chats."

    st.markdown(
        f"""
        <div style="background: #151821; border: 1px solid #283040; border-radius: 18px; padding: 1rem 1.4rem; margin-bottom: 1.5rem;">
            <div style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF; margin-bottom: 0.2rem;">{scope_title}</div>
            <div style="color: #9AA0A6; font-size: 0.88rem;">{scope_desc}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch cells for this scope
    cells = db.get_memories(scope=current_scope)

    # Insert top '+ Add Memory Cell'
    col_add_top, _ = st.columns([2.5, 7.5])
    with col_add_top:
        with st.popover("➕ Add Memory Cell", use_container_width=True):
            _render_new_cell_form(current_scope, insert_order=0)

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    if not cells:
        st.info("No active memory cells in this scope yet. Add your first cell above!", icon="💡")
    else:
        for idx, cell in enumerate(cells):
            ui_components.render_colab_memory_cell(
                cell=cell,
                index=idx,
                total_cells=len(cells),
                on_move_up=lambda c_id: _move_cell(cells, c_id, -1, current_scope),
                on_move_down=lambda c_id: _move_cell(cells, c_id, 1, current_scope),
                on_save=lambda c_id, t, b, exp: db.update_memory_cell(c_id, t, b, exp),
                on_delete=lambda c_id: _delete_cell_and_rerun(c_id),
            )

        # Bottom '+ Add Memory Cell'
        col_add_bot, _ = st.columns([2.5, 7.5])
        with col_add_bot:
            with st.popover("➕ Add Cell at Bottom", use_container_width=True):
                _render_new_cell_form(current_scope, insert_order=len(cells))


def _render_new_cell_form(scope: str, insert_order: int):
    """Form to insert a new memory cell."""
    st.markdown(f"**Insert New Memory Cell into {scope}**")
    title = st.text_input("Title (e.g. 🎯 Semester Goals)", key=f"new_cell_title_{scope}_{insert_order}")
    content = st.text_area("Content (Markdown)", height=120, key=f"new_cell_content_{scope}_{insert_order}")
    
    col_e1, col_e2 = st.columns([1, 1])
    with col_e1:
        has_exp = st.checkbox("Set Expiration Date", value=False, key=f"new_cell_has_exp_{scope}_{insert_order}")
    with col_e2:
        picked = st.date_input("Expires On", value=date.today() + timedelta(days=30), key=f"new_cell_date_{scope}_{insert_order}")

    if st.button("Commit Cell", key=f"commit_cell_{scope}_{insert_order}", type="primary"):
        if not title.strip() or not content.strip():
            st.error("Title and Content cannot be empty.")
        else:
            exp_iso = None
            if has_exp:
                exp_iso = datetime.combine(picked, datetime.min.time(), tzinfo=timezone.utc).isoformat()
            db.create_memory_cell(
                scope=scope,
                title=title,
                content=content,
                cell_order=insert_order,
                expires_at=exp_iso
            )
            st.success("Cell added!")
            st.rerun()


def _move_cell(cells: List[Dict[str, Any]], cell_id: str, offset: int, scope: str):
    """Moves a memory cell up or down in order."""
    ids = [c["id"] for c in cells]
    idx = ids.index(cell_id)
    new_idx = idx + offset
    if 0 <= new_idx < len(ids):
        ids[idx], ids[new_idx] = ids[new_idx], ids[idx]
        db.reorder_memory_cells(scope, ids)
        st.rerun()


def _delete_cell_and_rerun(cell_id: str):
    db.delete_memory_cell(cell_id)
    st.rerun()


# ====================================================================
# VIEW 3: ADVISORS MANAGEMENT PAGE (`👥` BUTTON)
# ====================================================================

def render_advisors_view():
    """
    Renders the Advisors roster page:
    - Circular colored avatar buttons for each Advisor
    - Dedicated chat launching
    - Advisor create & edit flow (Name, Icon, Color, System Instructions, Starter Memory Cells)
    """
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-weight: 700; color: #F0F3F8; margin-bottom: 0.25rem;">
                👥 AI Advisors Roster
            </h2>
            <p style="color: #9AA0A6; font-size: 0.95rem;">
                Create and manage specialized AI advisors. Each advisor carries dedicated system instructions and an isolated Memory Vault.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    advisors = db.get_advisors()

    # Roster display grid
    cols = st.columns(4)
    for idx, adv in enumerate(advisors):
        col = cols[idx % 4]
        adv_color = adv.get("color", "#4E80EE")
        adv_icon = adv.get("icon", "🤖")
        adv_id = adv["id"]

        with col:
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #1A1E28 0%, #13161F 100%); border: 1px solid #2B3344; border-radius: 20px; padding: 1.25rem; text-align: center; margin-bottom: 1.25rem; box-shadow: 0 4px 16px rgba(0,0,0,0.3);">
                    <div style="display: flex; justify-content: center; margin-bottom: 0.65rem;">
                        <div class="advisor-avatar-circle" style="background-color: {adv_color}25; border-color: {adv_color};">
                            {adv_icon}
                        </div>
                    </div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 1.05rem; margin-bottom: 0.35rem;">
                        {adv.get('name', 'Advisor')}
                    </div>
                    <div style="color: #9AA0A6; font-size: 0.8rem; height: 48px; overflow: hidden; margin-bottom: 0.85rem; line-height: 1.4;">
                        {adv.get('system_instructions', '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Chat button
            if st.button(f"💬 Chat with {adv.get('name')}", key=f"chat_adv_{adv_id}", type="primary", use_container_width=True):
                navigate_to("advisor_chat", advisor_id=adv_id)

            # Edit/Delete popover
            with st.popover("⚙️ Configure Advisor", use_container_width=True):
                _render_edit_advisor_form(adv)

    st.markdown("---")

    # Create New Advisor Section
    with st.expander("➕ Create New Advisor", expanded=(len(advisors) == 0)):
        _render_create_advisor_form()


def _render_create_advisor_form():
    """Form to define a new Advisor with starter memories."""
    col1, col2, col3 = st.columns([4, 2, 2])
    with col1:
        new_name = st.text_input("Advisor Name", placeholder="e.g. Strict University Tutor", key="new_adv_name")
    with col2:
        new_icon = st.text_input("Emoji / Icon", value="🎓", key="new_adv_icon")
    with col3:
        new_color = st.color_picker("Badge Accent Color", value="#4E80EE", key="new_adv_color")

    new_instructions = st.text_area(
        "Role / System Instructions",
        placeholder="You are my strict academic advisor. You emphasize mastery of fundamentals, step-by-step problem solving, and disciplined revision schedules.",
        height=120,
        key="new_adv_instructions"
    )

    st.markdown("**Optional Starter Memory Cell (Curriculum / Core Directives)**")
    starter_title = st.text_input("Starter Memory Title", placeholder="e.g. Semester Focus Topics", key="new_adv_starter_title")
    starter_content = st.text_area("Starter Memory Content", placeholder="List of current modules or project specifications...", height=80, key="new_adv_starter_content")

    if st.button("🚀 Create Advisor", type="primary", key="btn_commit_new_advisor"):
        if not new_name.strip():
            st.error("Please provide an Advisor Name.")
        else:
            adv = db.create_advisor(
                name=new_name,
                icon=new_icon,
                color=new_color,
                system_instructions=new_instructions
            )
            # Add starter memory cell if provided
            if starter_title.strip() and starter_content.strip():
                db.create_memory_cell(
                    scope=adv["id"],
                    title=starter_title,
                    content=starter_content,
                    cell_order=0
                )
            st.success(f"Advisor '{new_name}' created successfully!", icon="🎉")
            st.rerun()


def _render_edit_advisor_form(adv: Dict[str, Any]):
    """Form to edit or delete an existing Advisor."""
    adv_id = adv["id"]
    st.markdown(f"**Edit {adv.get('name')}**")
    edit_name = st.text_input("Name", value=adv.get("name", ""), key=f"edit_name_{adv_id}")
    edit_icon = st.text_input("Emoji", value=adv.get("icon", "🤖"), key=f"edit_icon_{adv_id}")
    edit_color = st.color_picker("Accent Color", value=adv.get("color", "#4E80EE"), key=f"edit_color_{adv_id}")
    edit_instructions = st.text_area("System Instructions", value=adv.get("system_instructions", ""), height=120, key=f"edit_inst_{adv_id}")

    col_save, col_del = st.columns([1, 1])
    with col_save:
        if st.button("Save", key=f"save_adv_{adv_id}", type="primary"):
            db.update_advisor(adv_id, edit_name, edit_icon, edit_color, edit_instructions)
            st.rerun()
    with col_del:
        if st.button("🗑️ Delete", key=f"del_adv_{adv_id}"):
            db.delete_advisor(adv_id)
            st.rerun()


# ====================================================================
# VIEW 4: SETTINGS PAGE (`⚙️` BUTTON)
# ====================================================================

def render_settings_view():
    """
    Renders the Settings page:
    - Multi-API-Key health and rotation diagnostic cards
    - Model selection (valid google-genai model IDs)
    - Google Search Grounding toggle
    - URL Context toggle
    - Supabase persistence status & schema instructions
    """
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-weight: 700; color: #F0F3F8; margin-bottom: 0.25rem;">
                ⚙️ System Settings & Multi-Key Health
            </h2>
            <p style="color: #9AA0A6; font-size: 0.95rem;">
                Configure Google GenAI models, inspect multi-API-key failover status, and verify cloud storage.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    settings = db.get_settings()

    # 1. Multi-API-Key Health & Status
    st.markdown("### 🔑 Multi-API-Key Pool & Failover Health")
    st.markdown(
        """
        Configure a pool of 2–3 keys in `.streamlit/secrets.toml` or Streamlit Cloud Secrets:
        ```toml
        GEMINI_API_KEYS = [
            "AIzaSyKeyOne...",
            "AIzaSyKeyTwo...",
            "AIzaSyKeyThree..."
        ]
        ```
        """
    )

    key_overview = ai_engine.get_key_status_overview()
    if key_overview:
        cols = st.columns(len(key_overview))
        for idx, k_info in enumerate(key_overview):
            with cols[idx]:
                status_color = "#34A853" if k_info["status"] == "Ready" else ("#4E80EE" if k_info["status"] == "Active" else "#EA4335")
                active_badge = "★ ACTIVE POINTER" if k_info["is_active"] else ""
                st.markdown(
                    f"""
                    <div style="background: #171A23; border: 1px solid #2B3344; border-radius: 16px; padding: 1rem; margin-bottom: 1rem;">
                        <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem;">{k_info['masked']}</div>
                        <div style="font-size: 0.8rem; color: {status_color}; font-weight: 600; margin-top: 0.25rem;">
                            Status: {k_info['status']}
                        </div>
                        <div style="font-size: 0.75rem; color: #8AB4F8; margin-top: 0.35rem; font-weight: 600;">
                            {active_badge}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("No Gemini API keys detected in Streamlit Secrets. You can test by entering a session key below.")

    # Paste temporary session key
    with st.expander("➕ Add Temporary Session API Key"):
        temp_key = st.text_input("Paste Gemini API Key", type="password", key="input_temp_gemini_key")
        if st.button("Add Key to Active Pool", key="btn_add_temp_key"):
            if temp_key.strip():
                if temp_key.strip() not in st.session_state["custom_api_keys"]:
                    st.session_state["custom_api_keys"].append(temp_key.strip())
                st.success("Key registered in current session pool!")
                st.rerun()

    st.markdown("---")

    # 2. Model Selection & Reasoning Configuration
    st.markdown("### 🧠 Gemini Model Selection")
    model_options = [
        "gemini-4-hydrogen",
        "gemini-4-argon",
        "gemini-4-carbon",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
    ]
    model_labels = {
        "gemini-4-hydrogen": "gemini-4-hydrogen (Default — Fast & High Reasoning with Thinking)",
        "gemini-4-argon": "gemini-4-argon (Balanced Deep Reasoning)",
        "gemini-4-carbon": "gemini-4-carbon (Maximum Reasoning & Complex Synthesis)",
        "gemini-3.5-flash-lite": "gemini-3.5-flash-lite (Ultra-Fast / Low Quota Consumption)",
        "gemini-2.5-flash": "gemini-2.5-flash (Legacy Fallback)",
    }

    current_model = settings.get("selected_model", "gemini-4-hydrogen")
    model_idx = model_options.index(current_model) if current_model in model_options else 0

    selected_model = st.selectbox(
        "Active Reasoning Model",
        options=model_options,
        index=model_idx,
        format_func=lambda m: model_labels.get(m, m),
        key="settings_model_selector"
    )

    st.markdown("---")

    # 3. Dynamic Tool Toggles
    st.markdown("### 🛠️ Google GenAI Tools")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        enable_search = st.toggle(
            "Enable Google Search Grounding",
            value=settings.get("enable_google_search", True),
            help="Enables real-time web search grounding and sources visualization.",
            key="settings_toggle_search"
        )
    with col_t2:
        enable_url = st.toggle(
            "Enable URL Context",
            value=settings.get("enable_url_context", True),
            help="Enables web URL reading within user prompts.",
            key="settings_toggle_url"
        )

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Settings", type="primary", key="btn_save_settings"):
        db.update_settings(
            selected_model=selected_model,
            enable_google_search=enable_search,
            enable_url_context=enable_url
        )
        st.success("Settings saved successfully!")
        st.rerun()

    st.markdown("---")

    # 4. Supabase Cloud Storage Status
    st.markdown("### ☁️ Persistent Supabase Storage")
    if db.is_supabase_connected():
        st.success("✅ Connected to Supabase Cloud Database", icon="⚡")
        st.caption("All Memory Cells, Advisors, Threads, and Messages are permanently synced to the cloud.")
    else:
        st.warning("⚠️ Running in Local Session Mode (Supabase secrets not found).")
        st.markdown(
            """
            To activate permanent cloud storage:
            1. Create a project at [supabase.com](https://supabase.com).
            2. Run `supabase_schema.sql` in your Supabase SQL Editor.
            3. Add your credentials to `.streamlit/secrets.toml`:
            ```toml
            SUPABASE_URL = "https://your-project.supabase.co"
            SUPABASE_KEY = "your-anon-key"
            ```
            """
        )


# ====================================================================
# MAIN ROUTER
# ====================================================================

current_page = st.session_state.get("current_page", "main_chat")

if current_page == "main_chat":
    render_chat_workspace(scope="main", advisor=None)

elif current_page == "advisor_chat":
    adv_id = st.session_state.get("selected_advisor_id")
    advisor = db.get_advisor(adv_id) if adv_id else None
    if not advisor:
        # Fallback to first advisor or main
        advisors = db.get_advisors()
        if advisors:
            advisor = advisors[0]
            st.session_state["selected_advisor_id"] = advisor["id"]
        else:
            advisor = None
    render_chat_workspace(scope=advisor["id"] if advisor else "main", advisor=advisor)

elif current_page == "memory_vault":
    render_memory_vault_view()

elif current_page == "advisors":
    render_advisors_view()

elif current_page == "settings":
    render_settings_view()
