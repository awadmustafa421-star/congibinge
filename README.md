# 🧠 Personal AI Advisor & Memory Vault (Google AI Studio Aesthetic)

A complete, production-ready Streamlit web application modeled after **Google AI Studio**, built specifically for a **GitHub → Streamlit Community Cloud** deployment workflow with **Supabase** for persistent cloud storage.

---

## ✨ Features & Architecture

- **Permanent Dark Mode & Rounded Ergonomics:** Modern charcoal/obsidian palette (`#0E1117`, `#13151A`, `#1B1F27`) with `border-radius: 16px` to `24px` on every element (zero sharp corners anywhere).
- **Symmetrical Top Navigation Bar:** Fixed header with 4 circular icon buttons and glowing active ring:
  - Top-Left: `🧠` **Memory Vault** & `👥` **Advisors**
  - Top-Right: `💬` **Main Chat** & `⚙️` **Settings**
- **Google Colab–Style Memory Vault:**
  - Distinct scopes: **Main Shared Memory** (shared across all chats) and **Advisor Isolated Memories** (private to each advisor).
  - Notebook cells featuring cell index badge `[1]`, editable Title, Expiry badge (`⏳ Expires: YYYY-MM-DD` or `♾️ Permanent`), Move Up `↑`, Move Down `↓`, in-place Markdown preview/editor, and Delete `🗑️`.
  - **Strict 100% Active Context:** No mute toggles. All active, non-expired cells are injected directly into the AI prompt context.
- **Automatic Expiry Cleanup:** Expired cells (`expires_at <= NOW()`) are automatically purged before queries and AI context assembly.
- **Multiple Saved Chat Threads:**
  - Independent thread management for Main Chat and each Advisor.
  - Automatic thread titling from the first user prompt.
  - Plain-text file context ingestion (`.txt`, `.md`, `.csv`, `.json`, `.py`, `.log`).
- **Google AI Studio Response View:**
  - **💭 Thinking Process:** Collapsible expander revealing inner reasoning trace (`part.thought`).
  - **Final Answer:** Clean Markdown rendering.
  - **🔍 Google Search Grounding:** Official search suggestion chips (`search_entry_point.rendered_content`) and clickable source pills (`grounding_chunks`).
  - **📌 Save to Memory Action:** Turn any helpful response into a permanent or timed memory cell in 1 click.
- **Smart Memory Proposal (Post-Response):**
  - Runs a fast background check using `gemini-3.5-flash-lite` to detect personal facts, preferences, study plans, or time-sensitive events (e.g., *"My dad is buying me headphones next week"* → auto-proposes an expiry date 7–10 days ahead).
  - Inline proposal card with `[Save]`, `[Edit]`, and `[Ignore]` actions.
- **Multi-API-Key Rotation & Failover (`ai_engine.py`):**
  - Round-robin rotation across 2–3 keys.
  - Automatic error catch (`429`, `RESOURCE_EXHAUSTED`, quota limit) with instant seamless failover to the next key.

---

## 📁 Repository Structure

```
.
├── .streamlit/
│   ├── config.toml           # Permanent dark theme & UI settings
│   └── secrets.toml.example  # Example template for local secrets
├── app.py                    # Main Streamlit entry point & view routing
├── styles.py                 # Google AI Studio CSS styling & rounded rules
├── db.py                     # Supabase database client, CRUD & expiry cleanup
├── ai_engine.py              # google-genai SDK wrapper, rotation, thinking & search
├── ui_components.py          # Colab cells, nav bar, thinking box, proposal card
├── supabase_schema.sql       # Ready-to-run PostgreSQL schema with RLS & seed data
├── requirements.txt          # Pinned compatible dependencies
└── README.md                 # Setup & deployment guide
```

---

## 🚀 Quick Setup & Deployment

### Step 1: Create and Configure Supabase
1. Create a free project at [supabase.com](https://supabase.com).
2. Open your Supabase Dashboard → **SQL Editor** → **New Query**.
3. Copy the contents of [`supabase_schema.sql`](supabase_schema.sql) and click **Run**.
   - This creates `advisors`, `memory_cells`, `chat_threads`, `chat_messages`, and `app_settings` tables with indexes and initial starter memories.
4. Go to **Project Settings** → **API** and copy:
   - **Project URL** (`https://xyzcompany.supabase.co`)
   - **Project API Keys** → `anon` `public` key.

---

### Step 2: Configure Streamlit Secrets

#### For Local Development:
Create a file at `.streamlit/secrets.toml`:

```toml
# Supabase Cloud Database Credentials
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Pool of 2-3 Gemini API Keys (for rotation and quota failover)
GEMINI_API_KEYS = [
    "AIzaSyYourFirstGeminiKeyHere",
    "AIzaSyYourSecondGeminiKeyHere",
    "AIzaSyYourThirdGeminiKeyHere"
]
```

#### For Streamlit Community Cloud Deployment:
1. Push this repository to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repository, branch (`main`), and set Main file path to `app.py`.
4. In **Advanced Settings → Secrets**, paste the exact TOML block above.
5. Click **Deploy**!

---

### Step 3: Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the Streamlit app
streamlit run app.py
```

---

## 🔑 Multi-API-Key Rotation & Reasoning Models

Supported Gemini Models in Settings:
- **`gemini-4-hydrogen`** *(Default)* — High-speed reasoning with active Thinking Process.
- **`gemini-4-argon`** — Balanced deep reasoning for architectural and strategic workflows.
- **`gemini-4-carbon`** — Maximum multi-step reasoning.
- **`gemini-3.5-flash-lite`** — Ultra-fast background analyzer for Memory Proposals.
- **`gemini-2.5-flash`** — Reliable fallback model.

---

## 🛡️ Graceful Offline & Demo Mode
If Supabase secrets or Gemini API keys have not been configured yet, the app runs in **Local Session Mode**:
- Preserves full interactive functionality in-memory with sample Advisors and Colab Memory Cells.
- Displays an intuitive setup banner pointing to the Settings page and `README.md`.
- Allows temporary session API key testing directly from the `⚙️ Settings` page.

---

## 📜 License
MIT License. Built for seamless personal productivity and high-signal intellectual workflows.
