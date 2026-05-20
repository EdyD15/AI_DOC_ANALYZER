import streamlit as st
import time
from styles import cyberpunk_styles
from services import (
    process_and_save_document, 
    get_all_documents_from_db, 
    clear_db, 
    query_openai_api
)

# Page Configuration
st.set_page_config(
    page_title="DocuMind AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Styles
st.markdown(cyberpunk_styles, unsafe_allow_html=True)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0  

# Extract current list of documents from ChromaDB
db_documents = get_all_documents_from_db()

# Sidebar - File Management
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=60)
    st.title("DocuMind Control")
    st.subheader("Document Upload")
    
    uploaded_file = st.file_uploader(
        "Upload corporate Document", 
        type=["pdf", "docx", "txt"], 
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_key}"
    )
    st.write("---")
    
    if uploaded_file is not None:
        if uploaded_file.name not in db_documents:
            # Call the function to extract pages, chunk them, and save to vector DB
            with st.spinner(f"Vectorizing & tracking pages for {uploaded_file.name}..."):
                success = process_and_save_document(uploaded_file)
                if success:
                    st.rerun() 

    if db_documents:
        st.success(f"Saved files: {len(db_documents)}")
        st.write("**Vector Knowledge Base:**")
        for fname in db_documents.keys():
            st.caption(f"📁 {fname}")
    else:
        st.info("Awaiting Document (PDF, DOCX, TXT)...")

    st.write("---")

    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
        
    if st.button("🗑️ Clear Database"):
        clear_db()
        st.session_state.uploader_key += 1
        st.rerun()

# Main Chat Interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
st.title("🤖 DocuMind AI Dashboard")
st.caption("Enterprise Hybrid Document Explorer")
st.write("---")

# Display older messages first
with st.container():
    for msg in st.session_state.messages:
        role = "👤 You:" if msg["role"] == "user" else "🤖 DocuMind:"
        row_class = "user-row" if msg["role"] == "user" else "ai-row"
        st.markdown(f'<div class="chat-row {row_class}"><strong>{role}</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)

# Chat Input
user_input = st.chat_input("Ask anything about the document or general questions...")
if user_input:
    # Display user message instantly
    st.markdown(f'<div class="chat-row user-row"><strong>👤 You:</strong><br>{user_input}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    try:
        # Create an empty placeholder to update the UI dynamically
        message_placeholder = st.empty()
        full_response = ""
        
        # Iterate through the chunks and update the custom HTML in real-time
        for chunk in query_openai_api(user_input):
            full_response += chunk
            # The '▌' symbol acts as a visual typing cursor
            message_placeholder.markdown(f'<div class="chat-row ai-row"><strong>🤖 DocuMind:</strong><br>{full_response}▌</div>', unsafe_allow_html=True)
            time.sleep(0.05) # Artificial delay to slow down the typing speed
            
        # Final render to remove the cursor once streaming is done
        message_placeholder.markdown(f'<div class="chat-row ai-row"><strong>🤖 DocuMind:</strong><br>{full_response}</div>', unsafe_allow_html=True)
        
        # Save the complete response to history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown('</div>', unsafe_allow_html=True)