import re
import html
import streamlit as st
from styles import app_styles
from services import (
    process_and_save_document,
    get_all_documents_from_db,
    clear_db,
    query_openai_api,
    generate_chat_export_docx,
    generate_chat_export_pdf,
    save_chat_session,
    load_all_chat_sessions,
    delete_chat_session
)

MAX_INPUT_LENGTH = 5000

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(app_styles, unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────
if "sessions" not in st.session_state:
    saved_sessions = load_all_chat_sessions()
    st.session_state.sessions = saved_sessions if saved_sessions else {"Chat 1": []}
    if not saved_sessions:
        save_chat_session("Chat 1", [])

if "current_session" not in st.session_state:
    sessions_list = list(st.session_state.sessions.keys())
    st.session_state.current_session = sessions_list[-1] if sessions_list else "Chat 1"

if "session_counter" not in st.session_state:
    existing_nums = [
        int(k.split(" ")[1])
        for k in st.session_state.sessions.keys()
        if k.startswith("Chat ") and len(k.split(" ")) == 2 and k.split(" ")[1].isdigit()
    ]
    st.session_state.session_counter = max(existing_nums) if existing_nums else 1

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "active_docs" not in st.session_state:
    st.session_state.active_docs = []
if "db_documents_cache" not in st.session_state:
    st.session_state.db_documents_cache = get_all_documents_from_db()

db_documents = st.session_state.db_documents_cache
available_files = list(db_documents.keys())

def refresh_documents():
    st.session_state.db_documents_cache = get_all_documents_from_db()

def safe_html(text):
    return html.escape(str(text)).replace("\n", "<br>")

def render_ai_response(text):
    text = html.escape(str(text))
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = text.replace("\n", "<br>")
    return text

@st.cache_data
def _cached_export_docx(messages: tuple) -> bytes:
    return generate_chat_export_docx([{"role": r, "content": c} for r, c in messages])

@st.cache_data
def _cached_export_pdf(messages: tuple) -> bytes:
    return generate_chat_export_pdf([{"role": r, "content": c} for r, c in messages])

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:

    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">📄</div>
        <span class="sidebar-brand-name">DocuMind</span>
    </div>
    """, unsafe_allow_html=True)

    # Chat history

    if st.button("+ New Chat", use_container_width=True):
        st.session_state.session_counter += 1
        new_chat_name = f"Chat {st.session_state.session_counter}"
        st.session_state.sessions[new_chat_name] = []
        st.session_state.current_session = new_chat_name
        save_chat_session(new_chat_name, [])
        st.rerun()

    selected_session = st.radio(
        "conversations",
        options=list(st.session_state.sessions.keys()),
        index=list(st.session_state.sessions.keys()).index(st.session_state.current_session),
        label_visibility="collapsed"
    )
    if selected_session != st.session_state.current_session:
        st.session_state.current_session = selected_session
        st.rerun()

    st.write("---")

    # Upload
    uploaded_file = st.file_uploader(
        "upload",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_key}"
    )
    if uploaded_file is not None and uploaded_file.name not in db_documents:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            success = process_and_save_document(uploaded_file)
            if success:
                refresh_documents()
                st.rerun()

    st.write("---")

    # Knowledge base
    if available_files:
        st.caption("Filter to specific files, or leave empty to search all.")
        st.session_state.active_docs = st.multiselect(
            "filter",
            options=available_files,
            default=[d for d in st.session_state.active_docs if d in available_files],
            label_visibility="collapsed",
            placeholder="All documents"
        )
        for fname in available_files:
            active = fname in st.session_state.active_docs
            icon = "🟢" if active else "📄"
            label = f"**{fname}**" if active else fname
            st.caption(f"{icon}  {label}")
    else:
        st.caption("No documents yet. Upload a PDF, DOCX, TXT, or image.")

    st.write("---")

    # Actions
    current_messages = st.session_state.sessions[st.session_state.current_session]

    if len(current_messages) > 0:
        export_format = st.radio("Export as:", ["Word (.docx)", "PDF (.pdf)"], horizontal=True)
        messages_key = tuple((m["role"], m["content"]) for m in current_messages)
        if export_format == "Word (.docx)":
            export_bytes = _cached_export_docx(messages_key)
            file_name = f"DocuMind_{st.session_state.current_session}.docx"
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            btn_label = "⬇ Download .docx"
        else:
            export_bytes = _cached_export_pdf(messages_key)
            file_name = f"DocuMind_{st.session_state.current_session}.pdf"
            mime_type = "application/pdf"
            btn_label = "⬇ Download .pdf"

        st.download_button(
            label=btn_label,
            data=export_bytes,
            file_name=file_name,
            mime=mime_type,
            use_container_width=True
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Delete Chat", use_container_width=True):
            delete_chat_session(st.session_state.current_session)
            del st.session_state.sessions[st.session_state.current_session]
            if len(st.session_state.sessions) == 0:
                st.session_state.session_counter = 1
                st.session_state.sessions = {"Chat 1": []}
                st.session_state.current_session = "Chat 1"
                save_chat_session("Chat 1", [])
            else:
                st.session_state.current_session = list(st.session_state.sessions.keys())[-1]
            st.rerun()
    with col2:
        if st.button("🧹 Clear Docs", use_container_width=True):
            clear_db()
            st.session_state.uploader_key += 1
            st.session_state.active_docs = []
            refresh_documents()
            st.rerun()

# ── Main area ──────────────────────────────────────────────────────
st.title("DocuMind AI")
st.caption(f"Active session: **{st.session_state.current_session}**  ·  {len(available_files)} document{'s' if len(available_files) != 1 else ''} in knowledge base")
st.write("---")

current_messages = st.session_state.sessions[st.session_state.current_session]

if not current_messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-title">What would you like to know?</div>
        <div class="empty-state-sub">Upload a document and ask anything about it, or start with a general question.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    anim_key = f"_seen_{st.session_state.current_session}"
    if anim_key not in st.session_state:
        st.session_state[anim_key] = len(current_messages)
    seen_count = st.session_state[anim_key]

    for i, msg in enumerate(current_messages):
        role_label = "You" if msg["role"] == "user" else "DocuMind AI"
        row_class = "user-row" if msg["role"] == "user" else "ai-row"
        new_class = " chat-row--new" if i >= seen_count else ""
        content = render_ai_response(msg["content"]) if msg["role"] == "assistant" else safe_html(msg["content"])
        st.markdown(
            f'<div class="chat-row {row_class}{new_class}"><strong>{role_label}</strong>{content}</div>',
            unsafe_allow_html=True
        )

    st.session_state[anim_key] = len(current_messages)

# ── Chat input ─────────────────────────────────────────────────────
user_input = st.chat_input("Ask a question about your documents...")
if user_input:
    if len(user_input) > MAX_INPUT_LENGTH:
        st.warning(f"Message too long ({len(user_input):,} chars). Keep it under {MAX_INPUT_LENGTH:,}.")
    else:
        st.markdown(
            f'<div class="chat-row user-row"><strong>You</strong>{safe_html(user_input)}</div>',
            unsafe_allow_html=True
        )

        current_session = st.session_state.current_session
        st.session_state.sessions[current_session].append({"role": "user", "content": user_input})
        save_chat_session(current_session, st.session_state.sessions[current_session])

        try:
            placeholder = st.empty()
            full_response = ""

            for chunk in query_openai_api(user_input, selected_documents=st.session_state.active_docs):
                full_response += chunk
                placeholder.markdown(
                    f'<div class="chat-row ai-row"><strong>DocuMind AI</strong>{render_ai_response(full_response)}<span class="cursor">▌</span></div>',
                    unsafe_allow_html=True
                )

            placeholder.markdown(
                f'<div class="chat-row ai-row"><strong>DocuMind AI</strong>{render_ai_response(full_response)}</div>',
                unsafe_allow_html=True
            )

            st.session_state.sessions[current_session].append({"role": "assistant", "content": full_response})
            save_chat_session(current_session, st.session_state.sessions[current_session])
            st.rerun()

        except Exception as e:
            st.session_state.sessions[current_session].pop()
            save_chat_session(current_session, st.session_state.sessions[current_session])
            st.error(f"Failed to get a response — {type(e).__name__}: {e}")
