import streamlit as st
from pypdf import PdfReader
import docx
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

# ==========================================
# 1. VECTOR DATABASE CONNECTION
# ==========================================

def get_chroma_collection():
    api_key = st.secrets["OPENAI_API_KEY"]
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key, model_name="text-embedding-3-small"
    )
    client = chromadb.PersistentClient(path="./vector_db")
    collection = client.get_or_create_collection(name="corporate_docs", embedding_function=openai_ef)
    return collection

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def clear_db():
    try:
        client = chromadb.PersistentClient(path="./vector_db")
        client.delete_collection("corporate_docs")
    except Exception:
        pass

def get_all_documents_from_db():
    try:
        collection = get_chroma_collection()
        result = collection.get(include=["metadatas"])
        unique_files = set([meta["source"] for meta in result["metadatas"] if "source" in meta])
        return {file: "Vectorized" for file in unique_files}
    except Exception:
        return {}

# ==========================================
# 2. READING, CHUNKING, AND PAGE TRACKING
# ==========================================

def process_and_save_document(uploaded_file):
    """Reads the document page by page, chunks it, and saves it with page numbers."""
    name = uploaded_file.name
    file_name = name.lower()
    collection = get_chroma_collection()

    # Check if document is already vectorized
    existing = collection.get(where={"source": name})
    if existing['ids']:
        return True 

    pages_data = [] # Stores dictionary: {"text": text, "page": page_number}
    
    try:
        if file_name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            for i, page in enumerate(reader.pages):
                ext = page.extract_text()
                # Extract text and save page index (i + 1)
                if ext: pages_data.append({"text": ext, "page": i + 1})
                
        elif file_name.endswith('.docx'):
            # Treat Word documents as "Page 1"
            doc = docx.Document(uploaded_file)
            full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            if full_text: pages_data.append({"text": full_text, "page": 1})
            
        elif file_name.endswith('.txt'):
            text = uploaded_file.read().decode('utf-8')
            if text: pages_data.append({"text": text, "page": 1})
            
    except Exception as e:
        st.error(f"Error reading file format: {e}")
        return False

    if not pages_data:
        return False

    all_chunks = []
    all_metadatas = []
    all_ids = []
    chunk_id_counter = 0

    # Iterate through each page
    for p_data in pages_data:
        # Chunk text strictly from the current page
        chunks = chunk_text(p_data["text"])
        for c in chunks:
            all_chunks.append(c)
            # Attach metadata with file name AND page number
            all_metadatas.append({"source": name, "page": p_data["page"]})
            all_ids.append(f"{name}_chunk_{chunk_id_counter}")
            chunk_id_counter += 1

    if all_chunks:
        collection.add(documents=all_chunks, metadatas=all_metadatas, ids=all_ids)
    return True

# ==========================================
# 3. QUERYING AND CITATIONS (ADVANCED RAG)
# ==========================================

def query_openai_api(user_question):
    collection = get_chroma_collection()
    
    # Request documents AND metadatas from ChromaDB
    results = collection.query(
        query_texts=[user_question],
        n_results=4, 
        include=["documents", "metadatas"]
    )
    
    # Build context by joining chunks with source and page on top
    context_parts = []
    if results['documents'] and results['documents'][0]:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            source = meta.get("source", "Unknown")
            page = meta.get("page", "N/A")
            context_parts.append(f"--- [SOURCE: {source} | PAGE: {page}] ---\n{doc}")
            
    context = "\n\n".join(context_parts)
    
    if context.strip():
        prompt = f"Based on the following document excerpts (which include source names and page numbers):\n\n{context}\n\nAnswer the user's question: {user_question}"
    else:
        prompt = user_question

    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are an advanced corporate document analyst. "
                    "When answering, you MUST base your response on the provided excerpts. "
                    "CRITICAL RULE: Whenever you use information from the excerpts, you MUST explicitly cite the exact Source and Page number provided in the context blocks. "
                    "Format your citations at the end of the sentence like this: '📝 [Document: X, Page: Y]'. "
                    "If the answer is NOT in the excerpts, do not hallucinate. Start with '🌐 [General Knowledge]:' and answer normally."
                )
            },
            {"role": "user", "content": prompt}
        ],
        stream=True # Enabled streaming
    )
    
    # Yield chunks dynamically for the typing effect
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content