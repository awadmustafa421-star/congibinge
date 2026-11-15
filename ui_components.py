"""
ui_components.py — Reusable UI Components.
Features:
- Symmetrical Top Navigation Bar with circular buttons and glowing active ring
- Google Colab-style Memory Cells (reordering, expiry picker, inline markdown editing)
- Thinking Process bar (Google AI Studio aesthetic)
- Google Search Grounding suggestions & source pills
- Smart Memory Proposal post-response card
- Manual 'Save to Memory' pin card
- Plain-text file attachment pill
- Multi-thread chat drawer / selector
"""

from datetime import datetime, timedelta, timezone, date
from typing import Dict, Any, List, Optional, Callable
import streamlit as st
import db


# ====================================================================
# 1. SYMMETRICAL TOP NAVIGATION BAR
# ====================================================================

def render_top_navbar(current_page: str, on_navigate: Callable[[str], None]):
    """
    Renders the fixed symmetrical top navigation bar:
    - Top-Left:  [🧠 Memory Vault] [👥 Advisors]
    - Center:    Brand Title & Active Mode Pill
    - Top-Right: [💬 Main Chat]   [⚙️ Settings]
    """
    col_left1, col_left2, col_center, col_right1, col_right2 = st.columns([1.1, 1.1, 6.0, 1.1, 1.1])

    # Left 1: Memory Vault (🧠)
    with col_left1:
        is_active = (current_page == "memory_vault")
        if st.button(
            "🧠",
            key="nav_btn_vault",
            help="Memory Vault (Google Colab UX)",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            on_navigate("memory_vault")

    # Left 2: Advisors (👥)
    with col_left2:
        is_active = (current_page == "advisors")
        if st.button(
            "👥",
            key="nav_btn_advisors",
            help="AI Advisors Roster",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            on_navigate("advisors")

    # Center Brand & Active Scope
    with col_center:
        active_advisor = st.session_state.get("selected_advisor")
        if current_page == "advisor_chat" and active_advisor:
            scope_badge = f"""
            <span class="brand-pill" style="border-color: {active_advisor.get('color', '#4E80EE')}; color: {active_advisor.get('color', '#4E80EE')};">
                {active_advisor.get('icon', '🤖')} {active_advisor.get('name', 'Advisor')}
            </span>
            """
        elif current_page == "memory_vault":
            scope_badge = '<span class="brand-pill">Vault Manager</span>'
        elif current_page == "advisors":
            scope_badge = '<span class="brand-pill">Advisors Suite</span>'
        elif current_page == "settings":
            scope_badge = '<span class="brand-pill">System Config</span>'
        else:
            scope_badge = '<span class="brand-pill">Shared Workspace</span>'

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; gap: 0.75rem; padding-top: 0.2rem;">
                <span style="font-weight: 700; font-size: 1.05rem; letter-spacing: -0.02em; color: #F0F3F8;">
                    Google AI Studio
                </span>
                <span style="color: #6E7681; font-weight: 300;">•</span>
                <span style="font-size: 0.92rem; color: #9AA0A6; font-weight: 500;">
                    Personal AI Advisor & Memory Vault
                </span>
                {scope_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Right 1: Main Chat (💬)
    with col_right1:
        is_active = (current_page == "main_chat")
        if st.button(
            "💬",
            key="nav_btn_chat",
            help="Main Personal Chat",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            on_navigate("main_chat")

    # Right 2: Settings (⚙️)
    with col_right2:
        is_active = (current_page == "settings")
        if st.button(
            "⚙️",
            key="nav_btn_settings",
            help="Settings & Multi-Key Health",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            on_navigate("settings")

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)


# ====================================================================
# 2. GOOGLE COLAB-STYLE MEMORY CELLS
# ====================================================================

def render_colab_memory_cell(
    cell: Dict[str, Any],
    index: int,
    total_cells: int,
    on_move_up: Callable[[str], None],
    on_move_down: Callable[[str], None],
    on_save: Callable[[str, str, str, Optional[str]], None],
    on_delete: Callable[[str], None]
):
    """
    Renders an individual memory cell modeled after Google Colab notebooks:
    - Index Badge: `[1]`
    - Editable Title & Expiry Badge
    - Move Up `↑`, Move Down `↓`, Edit `✏️`, Delete `🗑️`
    - In-place Markdown preview or Edit textarea + Expiry Date selector
    """
    cell_id = cell["id"]
    is_editing_key = f"editing_cell_{cell_id}"
    is_editing = st.session_state.get(is_editing_key, False)

    # Expiry calculation
    expires_at = cell.get("expires_at")
    expiry_badge = ""
    if expires_at:
        try:
            exp_clean = expires_at[:10]
            expiry_badge = f'<span class="expiry-badge-expiring">⏳ Expires: {exp_clean}</span>'
        except Exception:
            expiry_badge = '<span class="expiry-badge-expiring">⏳ Expiring Soon</span>'
    else:
        expiry_badge = '<span class="expiry-badge-permanent">♾️ Permanent</span>'

    with st.container():
        # Top Bar: Index Badge + Title + Expiry + Action Buttons
        col_badge, col_title, col_actions = st.columns([0.8, 6.2, 3.0])

        with col_badge:
            st.markdown(f'<span class="cell-index-badge">[{index + 1}]</span>', unsafe_allow_html=True)

        with col_title:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 0.65rem;">
                    <strong style="color: #F0F3F8; font-size: 1rem;">{cell.get('title', 'Untitled')}</strong>
                    {expiry_badge}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_actions:
            btn_up, btn_down, btn_edit, btn_del = st.columns([1, 1, 1.2, 1])
            with btn_up:
                if st.button("↑", key=f"up_{cell_id}", disabled=(index == 0), help="Move cell up"):
                    on_move_up(cell_id)
            with btn_down:
                if st.button("↓", key=f"down_{cell_id}", disabled=(index == total_cells - 1), help="Move cell down"):
                    on_move_down(cell_id)
            with btn_edit:
                edit_label = "✖" if is_editing else "✏️"
                if st.button(edit_label, key=f"edit_btn_{cell_id}", help="Edit memory cell"):
                    st.session_state[is_editing_key] = not is_editing
                    st.rerun()
            with btn_del:
                if st.button("🗑️", key=f"del_{cell_id}", help="Delete memory cell"):
                    on_delete(cell_id)

        # Body: In-place editor or Markdown preview
        if is_editing:
            with st.container():
                st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
                new_title = st.text_input("Title", value=cell.get("title", ""), key=f"title_in_{cell_id}")
                new_content = st.text_area("Memory Content (Markdown)", value=cell.get("content", ""), height=150, key=f"content_in_{cell_id}")

                col_exp1, col_exp2 = st.columns([2, 2])
                with col_exp1:
                    has_expiry = st.checkbox("Set Expiration Date", value=(expires_at is not None), key=f"has_exp_{cell_id}")
                with col_exp2:
                    default_date = date.today() + timedelta(days=14)
                    if expires_at:
                        try:
                            default_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).date()
                        except Exception:
                            pass
                    new_exp_date = None
                    if has_expiry:
                        picked_date = st.date_input("Expires on", value=default_date, key=f"date_in_{cell_id}")
                        new_exp_date = datetime.combine(picked_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()

                col_save, col_cancel = st.columns([2, 8])
                with col_save:
                    if st.button("💾 Save", key=f"save_btn_{cell_id}", type="primary"):
                        on_save(cell_id, new_title, new_content, new_exp_date)
                        st.session_state[is_editing_key] = False
                        st.rerun()
                with col_cancel:
                    if st.button("Cancel", key=f"cancel_btn_{cell_id}"):
                        st.session_state[is_editing_key] = False
                        st.rerun()
        else:
            # Markdown Content Preview
            st.markdown(
                f"""
                <div style="background: #141720; border: 1px solid #232835; border-radius: 14px; padding: 0.85rem 1.15rem; margin-top: 0.4rem; color: #D8DFEB; font-size: 0.93rem; line-height: 1.6;">
                """,
                unsafe_allow_html=True
            )
            st.markdown(cell.get("content", ""))
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)


# ====================================================================
# 3. THINKING PROCESS EXPANDER (GOOGLE AI STUDIO STYLE)
# ====================================================================

def render_thinking_process(thinking_text: Optional[str]):
    """
    Renders the extracted model thinking summary in a collapsible rounded box
    with subtle glowing cyan/blue aesthetics.
    """
    if not thinking_text:
        return

    with st.expander("💭 Thinking Process", expanded=False):
        st.markdown(
            f"""
            <div class="thinking-box">
                <div class="thinking-title">
                    <span>⚡ Model Reasoning Trace</span>
                </div>
                <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.85rem; color: #C5CBD6;">
{thinking_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ====================================================================
# 4. GOOGLE SEARCH GROUNDING & SOURCE PILLS
# ====================================================================

def render_grounding_results(search_html: Optional[str], sources: Optional[List[Dict[str, Any]]]):
    """
    Renders Google Search Grounding:
    - Official Search Suggestions HTML chips from search_entry_point.rendered_content
    - Clickable source pills from grounding_chunks
    """
    if not search_html and not sources:
        return

    st.markdown('<div class="grounding-container">', unsafe_allow_html=True)

    # If official rendered search HTML exists (chips/suggestions)
    if search_html:
        st.markdown('<div class="grounding-title">🔍 Google Search Suggestions</div>', unsafe_allow_html=True)
        # Render HTML safely
        st.components.v1.html(search_html, height=45, scrolling=False)

    # Clickable source pills
    if sources:
        st.markdown('<div class="grounding-title">🌐 Grounded Web Sources</div>', unsafe_allow_html=True)
        pills_html = '<div class="source-pill-grid">'
        for src in sources:
            title = src.get("title", "Source")
            uri = src.get("uri", "#")
            pills_html += f'<a href="{uri}" target="_blank" class="source-pill">🔗 {title}</a>'
        pills_html += '</div>'
        st.markdown(pills_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ====================================================================
# 5. SMART MEMORY PROPOSAL POPUP CARD
# ====================================================================

def render_memory_proposal_card(
    proposal: Dict[str, Any],
    scope_name: str,
    on_save: Callable[[str, str, Optional[str]], None],
    on_ignore: Callable[[], None]
):
    """
    Renders the post-response Smart Memory Proposal Card:
    - Header: 🧠 Save this to [Scope] Memory?
    - Preview of Title, Content, and Expiry Date
    - Action controls: [Save], [Edit], [Ignore]
    """
    is_editing = st.session_state.get("editing_proposal", False)
    suggested_days = proposal.get("suggested_expiry_days")

    # Suggested expiry text
    if suggested_days:
        calc_date = (date.today() + timedelta(days=int(suggested_days))).strftime("%Y-%m-%d")
        exp_preview = f"⏳ In {suggested_days} days ({calc_date})"
    else:
        exp_preview = "♾️ Permanent (No Expiry)"

    st.markdown(
        f"""
        <div class="memory-proposal-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-size: 1.3rem;">🧠</span>
                    <strong style="color: #F0F3F8; font-size: 1.05rem;">
                        Save this to {scope_name} Memory?
                    </strong>
                </div>
                <span class="proposal-badge">AI Proposal</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_editing:
        # Read-only preview
        st.markdown(
            f"""
            <div style="background: rgba(14, 17, 23, 0.6); border: 1px solid #283040; border-radius: 12px; padding: 0.85rem 1.1rem; margin-bottom: 0.85rem;">
                <div style="font-weight: 600; color: #8AB4F8; font-size: 0.95rem; margin-bottom: 0.35rem;">
                    {proposal.get('title', 'Memory Note')}
                </div>
                <div style="color: #C5CBD6; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0.45rem;">
                    {proposal.get('content', '')}
                </div>
                <div style="font-size: 0.78rem; color: #9AA0A6;">
                    Suggested Expiry: <strong style="color: #FDD663;">{exp_preview}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_save, col_edit, col_ignore, _ = st.columns([1.2, 1.2, 1.2, 4.4])
        with col_save:
            if st.button("✅ Save", key="prop_btn_save", type="primary", use_container_width=True):
                exp_date_iso = None
                if suggested_days:
                    dt = datetime.combine(date.today() + timedelta(days=int(suggested_days)), datetime.min.time(), tzinfo=timezone.utc)
                    exp_date_iso = dt.isoformat()
                on_save(proposal["title"], proposal["content"], exp_date_iso)
        with col_edit:
            if st.button("✏️ Edit", key="prop_btn_edit", use_container_width=True):
                st.session_state["editing_proposal"] = True
                st.rerun()
        with col_ignore:
            if st.button("❌ Ignore", key="prop_btn_ignore", use_container_width=True):
                on_ignore()

    else:
        # Inline edit mode
        edit_title = st.text_input("Title", value=proposal.get("title", ""), key="prop_edit_title")
        edit_content = st.text_area("Memory Content", value=proposal.get("content", ""), height=100, key="prop_edit_content")

        col_exp1, col_exp2 = st.columns([2, 2])
        with col_exp1:
            has_expiry = st.checkbox("Set Expiry Date", value=(suggested_days is not None), key="prop_edit_has_exp")
        with col_exp2:
            default_days = int(suggested_days) if suggested_days else 10
            default_d = date.today() + timedelta(days=default_days)
            picked_date = st.date_input("Expires On", value=default_d, key="prop_edit_date")

        col_save, col_cancel = st.columns([2, 8])
        with col_save:
            if st.button("💾 Confirm & Save", key="prop_btn_confirm", type="primary"):
                exp_iso = None
                if has_expiry:
                    dt = datetime.combine(picked_date, datetime.min.time(), tzinfo=timezone.utc)
                    exp_iso = dt.isoformat()
                on_save(edit_title, edit_content, exp_iso)
                st.session_state["editing_proposal"] = False
        with col_cancel:
            if st.button("Cancel", key="prop_btn_canceledit"):
                st.session_state["editing_proposal"] = False
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ====================================================================
# 6. MANUAL PIN MODAL / CARD
# ====================================================================

def render_manual_pin_card(
    message: Dict[str, Any],
    default_scope: str,
    advisors: List[Dict[str, Any]],
    on_save: Callable[[str, str, str, Optional[str]], None],
    on_cancel: Callable[[], None]
):
    """
    Renders an inline card allowing the user to manually convert any assistant
    message into a permanent or timed Memory Vault cell.
    """
    st.markdown(
        """
        <div class="memory-proposal-card" style="border-color: #8AB4F8;">
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.75rem;">
                <span style="font-size: 1.3rem;">📌</span>
                <strong style="color: #F0F3F8; font-size: 1.05rem;">
                    Pin Response to Memory Vault
                </strong>
            </div>
        """,
        unsafe_allow_html=True
    )

    # Pre-populate title from first few words or summary
    initial_title = "Pinned Insight: " + " ".join(message.get("content", "").split()[:5]) + "..."
    pin_title = st.text_input("Memory Title", value=initial_title, key="manual_pin_title")
    pin_content = st.text_area("Content", value=message.get("content", ""), height=150, key="manual_pin_content")

    # Scope selector
    scope_options = ["main"] + [a["id"] for a in advisors]
    scope_labels = ["Main Shared Vault"] + [f"Advisor: {a['name']}" for a in advisors]
    default_idx = scope_options.index(default_scope) if default_scope in scope_options else 0
    selected_scope = st.selectbox(
        "Save into Vault Scope",
        options=scope_options,
        index=default_idx,
        format_func=lambda s: scope_labels[scope_options.index(s)],
        key="manual_pin_scope"
    )

    col_exp1, col_exp2 = st.columns([2, 2])
    with col_exp1:
        has_expiry = st.checkbox("Set Expiration Date", value=False, key="manual_pin_has_exp")
    with col_exp2:
        picked_date = st.date_input("Expires On", value=date.today() + timedelta(days=14), key="manual_pin_date")

    col_confirm, col_cancel = st.columns([2, 8])
    with col_confirm:
        if st.button("📌 Save to Vault", key="btn_confirm_pin", type="primary"):
            exp_iso = None
            if has_expiry:
                dt = datetime.combine(picked_date, datetime.min.time(), tzinfo=timezone.utc)
                exp_iso = dt.isoformat()
            on_save(selected_scope, pin_title, pin_content, exp_iso)
    with col_cancel:
        if st.button("Cancel", key="btn_cancel_pin"):
            on_cancel()

    st.markdown("</div>", unsafe_allow_html=True)


# ====================================================================
# 7. FILE ATTACHMENT PILL
# ====================================================================

def render_file_attachment_pill(filename: Optional[str]):
    """Renders a rounded pill badge for uploaded plain-text files."""
    if not filename:
        return
    st.markdown(
        f"""
        <div class="chat-attachment-pill">
            <span>📎</span>
            <span>{filename}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ====================================================================
# 8. THREADS DRAWER / SELECTOR
# ====================================================================

def render_thread_selector(
    scope: str,
    active_thread_id: Optional[str],
    on_select_thread: Callable[[str], None],
    on_new_thread: Callable[[], None],
    on_rename_thread: Callable[[str, str], None],
    on_delete_thread: Callable[[str], None]
):
    """
    Renders the compact threads drawer / panel:
    - '+ New Chat' rounded button
    - Saved threads for the active workspace
    - Rename and Delete controls
    """
    threads = db.get_threads(scope=scope)

    # New Chat Button
    if st.button("➕ New Chat", key=f"btn_new_chat_{scope}", use_container_width=True, type="primary"):
        on_new_thread()
        st.rerun()

    st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)

    if not threads:
        st.caption("No saved threads yet.")
        return

    st.markdown(
        f"<div style='font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #8AB4F8; margin-bottom: 0.5rem;'>Saved Threads ({len(threads)})</div>",
        unsafe_allow_html=True
    )

    for thread in threads:
        t_id = thread["id"]
        is_active = (t_id == active_thread_id)
        title = thread.get("title", "Untitled Chat")

        col_t, col_menu = st.columns([8, 2])
        with col_t:
            # Active thread has glowing indicator
            label = f"▶ {title}" if is_active else f"💬 {title}"
            if st.button(
                label,
                key=f"th_btn_{t_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                on_select_thread(t_id)
                st.rerun()

        with col_menu:
            # Thread options expander/popover
            with st.popover("⋯", help="Thread options"):
                rename_val = st.text_input("Rename", value=title, key=f"ren_in_{t_id}")
                if st.button("Save Name", key=f"ren_save_{t_id}", type="primary"):
                    on_rename_thread(t_id, rename_val)
                    st.rerun()
                st.markdown("---")
                if st.button("🗑️ Delete", key=f"th_del_{t_id}"):
                    on_delete_thread(t_id)
                    st.rerun()
