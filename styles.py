"""
styles.py — Permanent Dark Mode + Google AI Studio Aesthetic Custom CSS.
Enforces generous rounded corners (16px to 24px) across every single element,
charcoal/obsidian palette, symmetrical top nav bar, Colab-style cells,
and glowing active states.
"""

DARK_THEME_CSS = """
<style>
/* ====================================================================
   GOOGLE AI STUDIO PALETTE & GLOBAL RESET
   ==================================================================== */
:root {
    --bg-main: #0E1117;
    --bg-surface: #13151A;
    --bg-card: #1B1F27;
    --bg-elevated: #222733;
    --border-subtle: #2A303C;
    --border-hover: #3E4758;
    --accent-blue: #4E80EE;
    --accent-glow: rgba(78, 128, 238, 0.45);
    --accent-cyan: #8AB4F8;
    --accent-green: #34A853;
    --accent-amber: #F9AB00;
    --text-primary: #F0F3F8;
    --text-secondary: #9AA0A6;
    --text-muted: #6E7681;
    --radius-sm: 12px;
    --radius-md: 18px;
    --radius-lg: 24px;
}

/* Force dark background and clean typography across entire app */
html, body, [data-testid="stAppViewContainer"], .main {
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* Hide Streamlit default header/footer elements for a native web-app look */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Container max width and padding */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1280px !important;
}

/* ====================================================================
   EVERYTHING ROUNDED: ALL STREAMLIT CORE CONTROLS
   ==================================================================== */

/* General Buttons */
div.stButton > button {
    border-radius: var(--radius-md) !important;
    background: linear-gradient(135deg, #1E232F 0%, #171A23 100%) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    padding: 0.55rem 1.25rem !important;
    font-weight: 500 !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
}

div.stButton > button:hover {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 12px var(--accent-glow) !important;
    transform: translateY(-1px) !important;
    color: #FFFFFF !important;
}

div.stButton > button:active {
    transform: translateY(1px) !important;
}

/* Primary Buttons */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3B6FD8 0%, #2955B5 100%) !important;
    border: 1px solid #4E80EE !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 10px rgba(78, 128, 238, 0.35) !important;
}

div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 18px rgba(78, 128, 238, 0.7) !important;
    border-color: #8AB4F8 !important;
}

/* Form Inputs, Text Areas, Select Boxes */
input[type="text"], input[type="password"], input[type="number"], textarea, .stSelectbox > div > div {
    border-radius: var(--radius-md) !important;
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

input[type="text"]:focus, textarea:focus, .stSelectbox > div > div:focus-within {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
    outline: none !important;
}

/* Chat Input Bar */
div[data-testid="stChatInput"] {
    border-radius: var(--radius-lg) !important;
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 16px var(--accent-glow) !important;
}

div[data-testid="stChatInput"] textarea {
    border-radius: var(--radius-lg) !important;
    background: transparent !important;
    border: none !important;
}

/* Expanders */
div.streamlit-expanderHeader, div[data-testid="stExpander"] {
    border-radius: var(--radius-md) !important;
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: all 0.2s ease !important;
}

div.streamlit-expanderHeader:hover {
    border-color: var(--border-hover) !important;
}

div[data-testid="stExpanderDetails"] {
    border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
    background-color: #141720 !important;
    border-top: 1px solid var(--border-subtle) !important;
}

/* Sidebar Containers */
section[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

section[data-testid="stSidebar"] > div {
    border-radius: var(--radius-lg) !important;
}

/* File Uploader */
div[data-testid="stFileUploader"] {
    border-radius: var(--radius-md) !important;
    background-color: var(--bg-surface) !important;
    border: 1px dashed var(--border-subtle) !important;
    padding: 0.75rem !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-blue) !important;
}

/* Cards, Metrics, Alerts */
div[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-subtle) !important;
    background-color: var(--bg-card) !important;
}

/* Radio buttons & segmented tabs */
div[role="radiogroup"] > label {
    border-radius: var(--radius-sm) !important;
    padding: 0.35rem 0.75rem !important;
    background-color: var(--bg-card) !important;
    margin-right: 0.5rem !important;
}

/* ====================================================================
   SYMMETRICAL TOP NAVIGATION BAR & CIRCULAR ICONS
   ==================================================================== */
.top-nav-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(19, 21, 26, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 0.65rem 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
}

.top-nav-group {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.brand-badge {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.95rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--text-primary);
}

.brand-pill {
    background: linear-gradient(135deg, rgba(78, 128, 238, 0.25) 0%, rgba(138, 180, 248, 0.15) 100%);
    border: 1px solid rgba(138, 180, 248, 0.4);
    color: var(--accent-cyan);
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    text-transform: uppercase;
}

/* ====================================================================
   CHAT WORKSPACE & MESSAGE BUBBLES
   ==================================================================== */
.chat-bubble-user {
    background: linear-gradient(135deg, #1F2533 0%, #191E2A 100%);
    border: 1px solid #323C50;
    border-radius: 20px 20px 4px 20px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    max-width: 90%;
    margin-left: auto;
}

.chat-bubble-assistant {
    background: linear-gradient(135deg, #171A22 0%, #12141B 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 20px 20px 20px 4px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.25rem;
    color: var(--text-primary);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
    max-width: 95%;
    margin-right: auto;
}

.chat-attachment-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background-color: rgba(78, 128, 238, 0.15);
    border: 1px solid rgba(78, 128, 238, 0.35);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: var(--accent-cyan);
    margin-bottom: 0.5rem;
}

/* ====================================================================
   THINKING PROCESS BAR (GOOGLE AI STUDIO STYLE)
   ==================================================================== */
.thinking-box {
    background: #11141C;
    border: 1px solid #2D3342;
    border-left: 3px solid #8AB4F8;
    border-radius: var(--radius-md);
    padding: 0.85rem 1.15rem;
    margin-bottom: 1rem;
    font-size: 0.88rem;
    line-height: 1.55;
    color: #BAC2D1;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.thinking-title {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-weight: 600;
    color: var(--accent-cyan);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.45rem;
}

/* ====================================================================
   GOOGLE SEARCH GROUNDING & SOURCES
   ==================================================================== */
.grounding-container {
    margin-top: 1rem;
    padding-top: 0.85rem;
    border-top: 1px solid #232734;
}

.grounding-title {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.5rem;
}

.source-pill-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.4rem;
}

.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background-color: #171A22;
    border: 1px solid var(--border-subtle);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    color: var(--accent-cyan);
    text-decoration: none;
    transition: all 0.2s ease;
}

.source-pill:hover {
    border-color: var(--accent-blue);
    background-color: #1E232F;
    box-shadow: 0 0 8px var(--accent-glow);
    color: #FFFFFF;
}

/* ====================================================================
   SMART MEMORY PROPOSAL CARD
   ==================================================================== */
.memory-proposal-card {
    background: linear-gradient(135deg, #181C26 0%, #12141B 100%);
    border: 1px solid #3E4B65;
    box-shadow: 0 6px 24px rgba(78, 128, 238, 0.22);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-top: 1rem;
    margin-bottom: 1.25rem;
    animation: fadeIn 0.3s ease-in-out;
}

.proposal-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(78, 128, 238, 0.2);
    border: 1px solid rgba(138, 180, 248, 0.4);
    border-radius: 999px;
    padding: 0.2rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--accent-cyan);
    text-transform: uppercase;
}

/* ====================================================================
   COLAB-STYLE MEMORY CELLS
   ==================================================================== */
.colab-cell {
    background: linear-gradient(180deg, #1B1F27 0%, #161920 100%);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.colab-cell:hover {
    border-color: var(--border-hover);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
}

.cell-index-badge {
    background: #232836;
    border: 1px solid #343C4F;
    color: var(--accent-cyan);
    font-family: monospace;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 0.15rem 0.5rem;
    border-radius: var(--radius-sm);
}

.expiry-badge-permanent {
    background: rgba(52, 168, 83, 0.15);
    border: 1px solid rgba(52, 168, 83, 0.4);
    color: #81C995;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
}

.expiry-badge-expiring {
    background: rgba(249, 171, 0, 0.15);
    border: 1px solid rgba(249, 171, 0, 0.4);
    color: #FDD663;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
}

/* ====================================================================
   ADVISOR CIRCLE BUTTONS & CARDS
   ==================================================================== */
.advisor-avatar-circle {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    border: 2px solid var(--border-subtle);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    cursor: pointer;
}

.advisor-avatar-circle:hover {
    transform: scale(1.08);
    box-shadow: 0 0 16px var(--accent-glow);
}

.advisor-avatar-circle.active {
    box-shadow: 0 0 0 3px #4E80EE, 0 0 18px rgba(78, 128, 238, 0.8);
    transform: scale(1.05);
}

/* Subtle fade in keyframes */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
"""
