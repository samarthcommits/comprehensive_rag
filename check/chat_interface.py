import streamlit as st
import time
import json
import os
from io import BytesIO
import pdfplumber
import pymupdf as fitz
from PIL import Image
import io
from langchain_google_genai import ChatGoogleGenerativeAI
from pymilvus import connections, utility
from utils.session_state import reset_retriever_state

def show():
    """Chat interface page"""
    
    if not st.session_state.setup_complete:
        st.warning("⚠️ Please set up a collection first in Document Management")
        if st.button("Go to Document Management"):
            st.switch_page("pages/document_management.py")
        return
    
    st.title("💬 Chat with Your Documents")
    st.markdown("Ask questions and get intelligent answers from your documents")
    
    # Sidebar configuration
    show_sidebar_config()
    
    # Main chat interface
    show_chat_interface()

def show_sidebar_config():
    """Sidebar with configuration options"""
    
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        # Current collection info
        st.info(f"""
        **User:** {st.session_state.config.get('user_name', 'N/A')}  
        **Collection:** {st.session_state.collection or 'N/A'}
        """)
        
        st.markdown("---")
        
        # Load PDF for current collection
        load_collection_pdfs()
        
        st.markdown("---")
        
        # Collection switcher
        if st.checkbox("🔄 Switch Collection"):
            show_collection_switcher()
        
        st.markdown("---")
        
        # Reset options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.context = []
                st.session_state.conte = []
                st.success("Chat cleared!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset All", use_container_width=True):
                reset_retriever_state()
                st.success("Reset complete!")
                st.rerun()

def load_collection_pdfs():
    """Load PDFs for the current collection"""
    
    try:
        file_path = f"documents/{st.session_state.user_name}/{st.session_state.collection}"
        
        if not os.path.exists(file_path):
            return
        
        pdf_names = os.listdir(file_path)
        
        if not pdf_names:
            st.warning("No PDFs found in collection")
            return
        
        # Get primary PDF name from database
        pdf_name = ''
        for suffix in ['ann', 'sparse', 'dense', 'rerank']:
            try:
                info = st.session_state.db_handler.get_collection_info(
                    user_name=st.session_state.user_name,
                    collection_name=f"{st.session_state.collection}_{suffix}"
                )
                if info and info.get('pdf_name'):
                    pdf_name = info['pdf_name']
                    break
            except:
                continue
        
        # Load all PDFs
        pdf_dict = {}
        doc_dict = {}
        
        for pdf_file in pdf_names:
            file_p = os.path.join(file_path, pdf_file)
            with open(file_p, "rb") as f:
                file_bytes = f.read()
            
            fake_uploaded_file = BytesIO(file_bytes)
            
            with pdfplumber.open(fake_uploaded_file) as pdf:
                pdf_dict[pdf_file] = pdf
            
            doc_dict[pdf_file] = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Store in session state
        st.session_state.pdf_dict = pdf_dict
        st.session_state.doc_dict = doc_dict
        
        # Set primary PDF if available
        if pdf_name and pdf_name in pdf_dict:
            st.session_state.pdf = pdf_dict[pdf_name]
            st.session_state.doc = doc_dict[pdf_name]
        
        st.success(f"📚 Loaded {len(pdf_names)} document(s)")
        
    except Exception as e:
        st.error(f"Error loading PDFs: {str(e)}")

def show_collection_switcher():
    """Allow switching between collections"""
    
    conn = connections.connect(
        db_name=st.session_state.config['user_name'],
        host="127.0.0.1",
        port="19530"
    )
    
    collections = utility.list_collections()
    
    selected_collection = st.selectbox(
        'Switch to Collection',
        options=collections,
        help="Select a different collection to chat with"
    )
    
    if selected_collection and st.button("Switch", use_container_width=True):
        try:
            collection_info = st.session_state.db_handler.get_collection_info(
                collection_name=selected_collection,
                user_name=st.session_state.config['user_name']
            )
            
            if collection_info:
                st.info(f"""
                **Retrieval:** {collection_info.get('retrieval_technique', 'N/A')}  
                **Chunking:** {collection_info.get('chunking_strategy', 'N/A')}
                """)
            
            st.session_state.collection = selected_collection
            st.success(f"Switched to: {selected_collection}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error switching collection: {str(e)}")

def show_chat_interface():
    """Main chat interface"""
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for idx, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message['role']):
                st.markdown(message['content'], unsafe_allow_html=True)
                
                # Show context for assistant messages
                if message['role'] == 'assistant' and 'conte' in message and message['conte']:
                    with st.expander(f"📄 View Source Context ({len(message['conte'])} pages)"):
                        for i, page_img in enumerate(message['conte'], start=1):
                            st.image(page_img, caption=f"Page {i}", use_container_width=True)
                            if i < len(message['conte']):
                                st.divider()
    
    # Chat input
    user_query = st.chat_input("💭 Ask a question about your documents...")
    
    if user_query:
        handle_user_query(user_query)

def handle_user_query(user_query):
    """Process user query and generate response"""
    
    # Add user message to history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_query
    })
    
    with st.spinner("🤔 Thinking..."):
        try:
            retriever = st.session_state.retriever_obj
            
            # Retrieve relevant documents
            start_time = time.perf_counter()
            retrieved_docs = retriever.get_all_results(user_query)
            retrieval_time = time.perf_counter() - start_time
            
            if not retrieved_docs:
                st.warning("⚠️ No relevant documents found in the collection")
                return
            
            # Process and highlight PDF pages
            imgs = process_pdf_highlights(retrieved_docs)
            
            # Prepare context
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            # Generate response using LLM
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.3,
                api_key=os.getenv("GOOGLE_API_KEY", "")
            )
            
            prompt = f"""Based on the following context, answer the user's question accurately and concisely.

Context:
{context}

Chat History:
{format_chat_history()}

Question: {user_query}

Answer:"""
            
            response = llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': answer,
                'context': [],
                'conte': imgs
            })
            
            # Show retrieval time
            st.toast(f"✅ Retrieved in {retrieval_time:.2f}s", icon="⚡")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

def process_pdf_highlights(retrieved_docs):
    """Process PDFs and highlight relevant sections"""
    
    imgs = []
    
    if not st.session_state.get('doc_dict'):
        return imgs
    
    try:
        # Organize pages by PDF
        page_pdf = {}
        for doc in retrieved_docs:
            try:
                doc.metadata['pages'] = json.loads(str(doc.metadata.get('pages', '[]')))
                pdf_name = doc.metadata.get('pdf_name', '')
                
                if not pdf_name or pdf_name not in st.session_state.doc_dict:
                    continue
                
                if pdf_name not in page_pdf:
                    page_pdf[pdf_name] = []
                
                page_pdf[pdf_name].extend(doc.metadata['pages'])
                page_pdf[pdf_name] = list(set(page_pdf[pdf_name]))
            except Exception as e:
                continue
        
        # Extract keywords for highlighting
        all_keywords = set()
        for doc in retrieved_docs:
            words = doc.page_content.split()
            keywords = [w.strip('.,!?;:') for w in words if len(w) > 4]
            all_keywords.update(keywords[:len(keywords) // 2])
        
        # Process each PDF and page
        for pdf_name in page_pdf:
            doc = st.session_state.doc_dict[pdf_name]
            
            for page_num in page_pdf[pdf_name]:
                try:
                    page = doc[page_num - 1]
                    
                    # Highlight keywords
                    for keyword in all_keywords:
                        text_instances = page.search_for(keyword)
                        for inst in text_instances:
                            highlight = page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=[1, 1, 0])
                            highlight.update()
                    
                    # Render page to image
                    pix = page.get_pixmap(dpi=300)
                    img_bytes = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_bytes))
                    imgs.append(img)
                except Exception as e:
                    continue
        
    except Exception as e:
        st.warning(f"Could not highlight PDFs: {str(e)}")
    
    return imgs

def format_chat_history():
    """Format chat history for LLM prompt"""
    
    history = []
    for msg in st.session_state.chat_history[-6:]:  # Last 3 exchanges
        role = msg['role']
        content = msg['content']
        history.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(history)