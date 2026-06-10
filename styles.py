app_styles = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* ── Design tokens ──────────────────────────────────────────────── */
:root {
    --bg:          oklch(99.5% 0.004 254);
    --bg-sidebar:  oklch(97%   0.005 254);
    --bg-raised:   oklch(95%   0.006 254);
    --bg-user:     oklch(95%   0.006 254);
    --border:      oklch(91%   0.007 254);
    --border-hov:  oklch(85%   0.009 254);
    --accent:      oklch(16%   0.003 254);
    --accent-hov:  oklch(24%   0.004 254);
    --accent-blue: oklch(58%   0.18  264);
    --accent-dim:  oklch(58%   0.18  264 / 0.12);
    --text:        oklch(10%   0.003 254);
    --text-2:      oklch(44%   0.009 254);
    --text-3:      oklch(50%   0.008 254);
}

/* ── Global font ─────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp, .stMarkdown,
input, button, textarea, select {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
}

/* ── Hide Streamlit chrome ───────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }

/* ── App background ─────────────────────────────────────────────── */
.stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}


/* ── Sidebar ────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 56px !important;
    transition: width 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                min-width 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                max-width 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 24px !important;
}

/* Collapse button: smooth flip transition */
[data-testid="stSidebarCollapseButton"] {
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

/* Mini-strip: flip the collapse button icon to point right */
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"] {
    transform: scaleX(-1) !important;
}

/* Center the sidebar header row and add breathing room */
[data-testid="stSidebarHeader"] {
    display: flex !important;
    align-items: center !important;
    padding: 12px 0 !important;
}

/* ── Sidebar mini-strip when collapsed ───────────────────────────── */
[data-testid="stSidebar"][aria-expanded="false"] {
    width: 56px !important;
    min-width: 56px !important;
    max-width: 56px !important;
    transform: none !important;
    overflow: hidden !important;
}

/* In mini mode: center the icon, hide the name */
[data-testid="stSidebar"][aria-expanded="false"] .sidebar-brand {
    justify-content: center !important;
    padding: 12px 0 12px 0 !important;
    border-bottom: 1px solid var(--border) !important;
    margin-bottom: 0 !important;
}

[data-testid="stSidebar"][aria-expanded="false"] .sidebar-brand-name { display: none !important; }

/* Hide all interactive content in mini mode */
[data-testid="stSidebar"][aria-expanded="false"] .stButton,
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stRadio"],
[data-testid="stSidebar"][aria-expanded="false"] .stCaption,
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stFileUploader"],
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stMultiSelect"],
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stDownloadButton"],
[data-testid="stSidebar"][aria-expanded="false"] hr,
[data-testid="stSidebar"][aria-expanded="false"] p {
    display: none !important;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 4px 20px 4px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}

.sidebar-brand-icon {
    width: 28px;
    height: 28px;
    background: var(--accent);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    flex-shrink: 0;
}

.sidebar-brand-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.1px;
}


/* ── Main title ─────────────────────────────────────────────────── */
.stApp h1 {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: -0.3px !important;
    background: none !important;
    -webkit-text-fill-color: var(--text) !important;
    text-align: left !important;
    padding-top: 0 !important;
    margin-bottom: 2px !important;
}

.stCaption, .stCaption p {
    color: var(--text-2) !important;
    font-size: 13px !important;
    text-align: left !important;
}

/* ── Empty state ─────────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 96px 24px 60px;
    max-width: 520px;
    margin: 0 auto;
}

.empty-state-title {
    font-size: 26px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 10px;
    letter-spacing: -0.4px;
    line-height: 1.25;
}

.empty-state-sub {
    font-size: 14.5px;
    color: var(--text-2);
    line-height: 1.6;
}

/* ── Chat bubbles ───────────────────────────────────────────────── */
.chat-row {
    font-size: 14.5px;
    line-height: 1.7;
    color: var(--text);
    margin-bottom: 4px;
}

.chat-row--new {
    animation: fadeSlide 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* User: right-aligned bubble */
.user-row {
    background-color: var(--bg-user);
    border: none;
    border-radius: 18px;
    padding: 11px 16px;
    width: fit-content;
    max-width: 58%;
    margin-left: auto;
    margin-bottom: 12px;
    position: relative;
}

.user-row strong {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* AI: no card, left-aligned, just text */
.ai-row {
    background: none;
    border: none;
    border-radius: 0;
    padding: 4px 0 16px 0;
    max-width: 100%;
}

.ai-row strong {
    color: var(--text-3);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: block;
    margin-bottom: 6px;
}

.ai-row code {
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 13px;
    color: var(--text);
    font-family: 'Cascadia Code', 'Fira Code', ui-monospace, monospace !important;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border: 1px solid var(--border) !important;
    background-color: var(--bg) !important;
    color: var(--text-2) !important;
    padding: 6px 12px !important;
    white-space: nowrap !important;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
    width: 100%;
}

.stButton > button:hover {
    background-color: var(--bg-raised) !important;
    border-color: var(--border-hov) !important;
    color: var(--text) !important;
}

.stButton > button:active,
[data-testid="stDownloadButton"] > button:active {
    opacity: 0.85 !important;
}

/* New Chat — primary */
[data-testid="stSidebar"] .stButton:first-of-type > button {
    background-color: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] .stButton:first-of-type > button:hover {
    background-color: var(--accent-hov) !important;
    border-color: var(--accent-hov) !important;
}

/* ── Focus indicators (keyboard nav) ────────────────────────────── */
.stButton > button:focus-visible,
[data-testid="stDownloadButton"] > button:focus-visible {
    outline: 2px solid var(--accent-blue) !important;
    outline-offset: 2px !important;
    box-shadow: 0 0 0 4px var(--accent-dim) !important;
}

[data-testid="stChatInputSubmitButton"] > button:focus-visible {
    outline: 2px solid var(--accent-blue) !important;
    outline-offset: 2px !important;
}

/* ── Download button ─────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    background-color: var(--bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-2) !important;
    width: 100%;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
}

[data-testid="stDownloadButton"] > button:hover {
    background-color: var(--bg-raised) !important;
    border-color: var(--border-hov) !important;
    color: var(--text) !important;
}

/* ── File uploader ───────────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    border: 1.5px dashed var(--border) !important;
    border-radius: 9px !important;
    background-color: var(--bg) !important;
    transition: border-color 0.15s ease, background-color 0.15s ease !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent-blue) !important;
    background-color: var(--bg-raised) !important;
}

/* ── Multiselect ─────────────────────────────────────────────────── */
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background-color: var(--bg-raised) !important;
    border-radius: 5px !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-size: 12px !important;
}

/* ── Radio ───────────────────────────────────────────────────────── */
[data-testid="stRadio"] label p {
    font-size: 13px !important;
    color: var(--text-2) !important;
}

[data-testid="stRadio"] label:has(input:checked) {
    background-color: var(--accent-dim) !important;
    border-radius: 5px !important;
}

[data-testid="stRadio"] label:has(input:checked) p {
    color: var(--text) !important;
    font-weight: 500 !important;
}

/* ── Divider ─────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 14px 0 !important;
}

/* ── Alerts ──────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-size: 13px !important;
}

/* ── Spinner ─────────────────────────────────────────────────────── */
[data-testid="stSpinner"] p {
    font-size: 13px !important;
    color: var(--text-2) !important;
}

/* ── Chat input ──────────────────────────────────────────────────── */
section[data-testid="stBottom"] {
    background: var(--bg) !important;
    border-top: none !important;
    padding: 16px 0 24px !important;
}

/* Wipe all backgrounds/borders inside stBottom (low specificity — overridden below) */
section[data-testid="stBottom"] *,
section[data-testid="stBottom"]:focus-within * {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

/* stChatInput is the pill — specificity 0-2-1 beats the clear above (0-1-1) */
section[data-testid="stBottom"] [data-testid="stChatInput"] {
    position: relative !important;
    border-radius: 26px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg) !important;
    background-color: var(--bg) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

section[data-testid="stBottom"] [data-testid="stChatInput"]:focus-within {
    border-color: var(--border-hov) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.10) !important;
}

/* Textarea inside is transparent — the pill comes from stChatInput above */
section[data-testid="stBottom"] [data-testid="stChatInput"] textarea {
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    background-color: transparent !important;
    color: var(--text) !important;
    font-size: 16px !important;
    padding: 14px 56px 14px 20px !important;
    box-shadow: none !important;
    resize: none !important;
    outline: none !important;
}

section[data-testid="stBottom"] [data-testid="stChatInput"] textarea:focus,
section[data-testid="stBottom"] [data-testid="stChatInput"] textarea:focus-visible {
    outline: none !important;
}

section[data-testid="stBottom"] [data-testid="stChatInputSubmitButton"] {
    position: absolute !important;
    right: 12px !important;
    bottom: 9px !important;
    transform: none !important;
    z-index: 1 !important;
}

section[data-testid="stBottom"] [data-testid="stChatInputSubmitButton"] > button {
    background-color: var(--accent) !important;
    border-radius: 50% !important;
    border: none !important;
    width: 34px !important;
    height: 34px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background-color 0.15s ease !important;
}

section[data-testid="stBottom"] [data-testid="stChatInputSubmitButton"] > button:hover {
    background-color: var(--accent-hov) !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-hov); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-2); }

/* ── Streaming cursor ────────────────────────────────────────────── */
.cursor {
    display: inline-block;
    animation: blink 0.7s step-end infinite;
    margin-left: 1px;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
}

/* ── Mobile (≤640px) ────────────────────────────────────────────── */
@media (max-width: 640px) {
    /* Wider message bubbles — 58% is too narrow on a phone */
    .user-row {
        max-width: 82% !important;
    }

    /* 44px touch targets for all tappable controls */
    .stButton > button,
    [data-testid="stDownloadButton"] > button {
        min-height: 44px !important;
        padding: 10px 14px !important;
    }

    /* Less top breathing room in empty state on short screens */
    .empty-state {
        padding: 48px 20px 40px !important;
    }

    /* Let Streamlit handle sidebar collapse natively on mobile —
       the desktop mini-strip (56px) makes no sense in an overlay context */
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: unset !important;
        min-width: unset !important;
        max-width: unset !important;
        transform: unset !important;
        overflow: unset !important;
    }
}

/* ── Reduced motion ─────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""
